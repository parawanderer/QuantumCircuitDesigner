from collections import deque
from typing import Callable
import numpy as np
from base.models import CircuitDefinition, MultiOperationType, OperationType, QuBitOperationBase, QuBitOperationMultiParam, QuBitOperationSingleParam

# def _cnot(n: int, control: int, target: int):
#     # Used this as a reference to generate this dynamically for arbitrary target & control qubits
#     # https://quantumcomputing.stackexchange.com/a/5192

#     cnot1 = np.array(1, dtype=complex)
#     cnot2 = np.array(1, dtype=complex)

#     # if the control-th qubit is 0, leave the target-th qubit alone
#     # if the control-th qubit is 1, apply X to the target-th qubit

#     for i in range(0, n):
#         if i == control:
#             cnot1 = np.kron(cnot1, (QuantumComputer.BRA_0 @ QuantumComputer.KET_0))
#             cnot2 = np.kron(cnot2, (QuantumComputer.BRA_1 @ QuantumComputer.KET_1))
#         elif i == target:
#             cnot1 = np.kron(cnot1, QuantumComputer.IDENTITY)
#             cnot2 = np.kron(cnot2, QuantumComputer.SINGLE_MAPPINGS[OperationType.X])
#         else:
#             cnot1 = np.kron(cnot1, QuantumComputer.IDENTITY)
#             cnot2 = np.kron(cnot2, QuantumComputer.IDENTITY)
    
#     return cnot1 + cnot2

# def _cz(n: int, control: int, target: int):
#     # essentially based on the above pattern with _cnot
#     cz1 = np.array(1, dtype=complex)
#     cz2 = np.array(1, dtype=complex)

#     # if the control-th qubit is 0, leave the target-th qubit alone
#     # if the control-th qubit is 1, apply Z to the target-th qubit

#     for i in range(0, n):
#         if i == control:
#             cz1 = np.kron(cz1, (QuantumComputer.BRA_0 @ QuantumComputer.KET_0))
#             cz2 = np.kron(cz2, (QuantumComputer.BRA_1 @ QuantumComputer.KET_1))
#         elif i == target:
#             cz1 = np.kron(cz1, QuantumComputer.IDENTITY)
#             cz2 = np.kron(cz2, QuantumComputer.SINGLE_MAPPINGS[OperationType.Z])
#         else:
#             cz1 = np.kron(cz1, QuantumComputer.IDENTITY)
#             cz2 = np.kron(cz2, QuantumComputer.IDENTITY)
    
#     return cz1 + cz2

def _produceGenericNotGateFn(singleGate):
    """
    Produce a callback to dynamically build the *conditional gate* of type *singleGate*
    """

    # Used this as a reference to generate this dynamically for arbitrary target & control qubits
    # https://quantumcomputing.stackexchange.com/a/5192

    def fn(n: int, control: int, target: int):
        m1 = np.array(1, dtype=complex)
        m2 = np.array(1, dtype=complex)

        # if the control-th qubit is 0, leave the target-th qubit alone
        # if the control-th qubit is 1, apply *singleGate* to the target-th qubit

        for i in range(0, n):
            if i == control:
                m1 = np.kron(m1, (QuantumComputer.BRA_0 @ QuantumComputer.KET_0))
                m2 = np.kron(m2, (QuantumComputer.BRA_1 @ QuantumComputer.KET_1))
            elif i == target:
                m1 = np.kron(m1, QuantumComputer.IDENTITY)
                m2 = np.kron(m2, singleGate)
            else:
                m1 = np.kron(m1, QuantumComputer.IDENTITY)
                m2 = np.kron(m2, QuantumComputer.IDENTITY)
    
        return m1 + m2

    return fn


def _swap(n: int, control: int, target: int):
    # Leveraged this idea: https://quantumcomputing.stackexchange.com/a/24051
    # cnot1 = _cnot(n, control, target)
    # cnot2 = _cnot(n, target, control)
    cnot_callback = QuantumComputer.MULTI_MAPPINGS[MultiOperationType.CNOT]
    cnot1 = cnot_callback(n, control, target)
    cnot2 = cnot_callback(n, target, control)
    return cnot1 @ cnot2 @ cnot1

class QuantumComputer:
    """A computation simulator for a quantum circuit definition"""

    KET_0 = np.array([[1, 0]], dtype=complex)
    BRA_0 = np.array([[1], [0]], dtype=complex)
    KET_1 = np.array([[0, 1]], dtype=complex)
    BRA_1 = np.array([[0], [1]], dtype=complex)

    IDENTITY = np.eye(2, dtype=complex)

    SINGLE_MAPPINGS: dict[OperationType, any] = {
        OperationType.MEASURE: IDENTITY,
        OperationType.X: np.array([
            [0, 1],
            [1, 0]
        ], dtype=complex),
        OperationType.Y: np.array([
            [0, 0 -1j],
            [0 + 1j, 0]
        ], dtype=complex),
        OperationType.Z: np.array([
            [1, 0],
            [0, -1]
        ], dtype=complex),
        OperationType.H: (1/np.sqrt(2)) * np.array([
            [1, 1],
            [1, -1]
        ], dtype=complex),
        OperationType.S: np.array([
            [1, 0],
            [0, 0 + 1j]
        ], dtype=complex),
        OperationType.T: np.array([
            [1, 0],
            [0, np.exp(np.pi * (1j) / 4)]
        ], dtype=complex),
        OperationType.T_dg: np.conjugate(np.array([
            [1, 0],
            [0, np.exp(np.pi * (1j) / 4)]
        ], dtype=complex)),
    }
    MULTI_MAPPINGS : dict[MultiOperationType, Callable[[int, int, int], any]] = {
        MultiOperationType.CNOT: _produceGenericNotGateFn(SINGLE_MAPPINGS[OperationType.X]), #_cnot,
        MultiOperationType.CZ: _produceGenericNotGateFn(SINGLE_MAPPINGS[OperationType.Z]), #_cz,
        MultiOperationType.CS: _produceGenericNotGateFn(SINGLE_MAPPINGS[OperationType.S]),
        MultiOperationType.SWAP: _swap
    }

    def __init__(self, circuit: CircuitDefinition) -> None:
        self._circuit = circuit
    
    def compute(self, start_vector: list[float]):
        current = np.array(start_vector, dtype=complex)

        ordered_operations = self._convert_operations_list()
        # we can ignore the last one as that one is always the single "measure" which is not handled in any special way for now
        ordered_operations = ordered_operations[:-1]
        num_qubits = self._circuit.num_qubits

        # it may very well be possible to optimize this bit
        for operations in ordered_operations: 
            # from left to right on the circuit diagram
            # needs to be converted into a tensor product. 
            # Let's ignore the multi for now and focus on converting single...
            multi_compositions = []
            tensor_prod = np.array([[1]], dtype=complex)

            # compose single gates via tensor product
            for i in range(0, num_qubits):
                if operations and operations[0][0] == i:
                    (matrix, multi_matrix) = QuantumComputer._get_next_matrix(operations, num_qubits)
                    if multi_matrix is not None:
                        multi_compositions.append(multi_matrix) # this will be composed later as it's not super obvious what to do when there's a lot of operations on one line of time
                else:
                    matrix = QuantumComputer.IDENTITY
                tensor_prod = np.kron(tensor_prod, matrix)
            
            final_matrix = tensor_prod
            for extra_matrix in multi_compositions: # compose the multi-operations onto the tensor product of the single operations
                # which is essentially the same as if the operations were defined at multiple different times
                # so this is algebraically correct as far as the matrix product is concerned (going from right to left)
                # but there might be a trick to count this inside of the above loop already that I am not aware of
                final_matrix = extra_matrix @ final_matrix

            # this final matrix is now applied for the given "step"
            current = final_matrix @ current
        
        return current


    @staticmethod
    def _get_next_matrix(operations: list[tuple[int, QuBitOperationBase]], n: int) -> tuple[object, object]:
        qubit, operation = operations.popleft()
        if isinstance(operation, QuBitOperationSingleParam):
            return (QuantumComputer.SINGLE_MAPPINGS[operation.get_type()], None)
        elif isinstance(operation, QuBitOperationMultiParam):
            return (QuantumComputer.IDENTITY, QuantumComputer.MULTI_MAPPINGS[operation.get_type()](n, operation.get_applies_to(), operation.get_applied_by()))
        else:
            return (QuantumComputer.IDENTITY, None)

    def _convert_operations_list(self):
        # [time, (qubit, operation)]
        result: dict[int, deque[tuple[int, QuBitOperationBase]]] = {}

        for qubit, timeline in enumerate(self._circuit.operation_schedules):
            for time, op in timeline.operations.items():
                if time not in result:
                    result[time] = deque()

                result[time].append((qubit, op))
        
        # sorted by time
        sorted_result = list(result.items())
        sorted_result.sort(key=lambda v: v[0])
        
        # time doesn't matter anymore, only order
        return [operations for time, operations in sorted_result]