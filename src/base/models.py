from abc import ABC, abstractmethod
from enum import Enum
from typing import Any
import heapq


class OperationType(Enum):
    H = 1
    X = 2
    Y = 3
    T = 4
    S = 5
    MEASURE = 6
    Z = 7
    T_dg = 8


class MultiOperationType(Enum):
    CNOT = 1,
    CZ = 2,
    SWAP = 3,
    CS = 4


class DefinitionVisitor(ABC):
    @abstractmethod
    def handle_single_param_op(self, op: 'QuBitOperationSingleParam') -> Any:
        ...

    @abstractmethod
    def handle_multi_param_op(self, op: 'QuBitOperationMultiParam') -> Any:
        ...

    @abstractmethod
    def handle_multi_param_ref(self, op: 'QuBitOperationMultiParamReference') -> Any:
        ...


class QuBitOperationBase(ABC):
    @abstractmethod
    def accept(self, visitor: DefinitionVisitor) -> Any:
        ...

    @abstractmethod
    def get_type_name(self) -> str:
        ...


class QuBitOperationMultiParam(QuBitOperationBase):
    def __init__(self, operation_type: MultiOperationType, applies_to_qbit: int, of_qubit: int):
        self._type = operation_type
        self._applies_to_qubit = applies_to_qbit
        self._of_qubit = of_qubit

    def get_type(self) -> MultiOperationType:
        return self._type

    def get_type_name(self) -> str:
        return self._type.name

    def get_applies_to(self) -> int:
        return self._applies_to_qubit

    def get_applied_by(self) -> int:
        return self._of_qubit

    def accept(self, visitor: DefinitionVisitor) -> Any:
        return visitor.handle_multi_param_op(self)

    def set_applied_by(self, applied_by_qubit: int) -> None:
        self._of_qubit = applied_by_qubit

    def set_applies_to(self, applies_to_qubit: int):
        self._applies_to_qubit = applies_to_qubit

    def __str__(self):
        return f"{self._type.name}(by={self._of_qubit},applies_to=q{self._applies_to_qubit})"


class QuBitOperationSingleParam(QuBitOperationBase):
    def __init__(self, operation_type: OperationType):
        self._type = operation_type

    def get_type(self) -> OperationType:
        return self._type

    def get_type_name(self) -> str:
        return self._type.name

    def accept(self, visitor: DefinitionVisitor):
        return visitor.handle_single_param_op(self)

    def __str__(self):
        return f"{self._type.name}"


class QuBitOperationMultiParamReference(QuBitOperationBase):
    def __init__(self, pointer: QuBitOperationMultiParam):
        self._pointer = pointer

    def accept(self, visitor: DefinitionVisitor) -> Any:
        return visitor.handle_multi_param_ref(self)

    def get_type_name(self) -> str:
        return self._pointer.get_type_name()

    def refers_to(self):
        return self._pointer

    def __str__(self):
        return f"{self._pointer.get_type_name()}(on self)"


class QuBitOperations:
    def __init__(self, qbit: int):
        self._for_qubit = qbit
        self._operations: dict[int, QuBitOperationBase] = {}
        self._last_time: int = -1
        self._times = set()

    def add_operation(self, operation: OperationType, time: int = None):
        time_slot_to_define = time if time is not None else (self._last_time + 1)
        op = QuBitOperationSingleParam(operation)
        self._operations[time_slot_to_define] = op
        self._update_last_time(time_slot_to_define)
        return (op, time_slot_to_define)

    def add_multi_operation(self, operation: MultiOperationType, qbit: int, time: int = None):
        time_slot_to_define = time if time is not None else (self._last_time + 1)
        op = QuBitOperationMultiParam(operation, qbit, self._for_qubit)
        self._operations[time_slot_to_define] = op
        self._update_last_time(time_slot_to_define)
        return (op, time_slot_to_define)

    def add_some_operation(self, operation: QuBitOperationBase, time: int):
        self._operations[time] = operation
        self._update_last_time(time)

    def drop_operation(self, time: int):
        if time not in self._operations:
            raise ValueError(f"Operation not defined at time {time} for qubit={self._for_qubit}")

        self._times.remove(time)

        operation = self._operations[time]
        del self._operations[time]
        return operation

    def add_participation(self, operation: QuBitOperationMultiParam, time: int):
        op = QuBitOperationMultiParamReference(operation)
        self._operations[time] = op
        self._update_last_time(time)

    def _update_last_time(self, time: int):
        self._last_time = max(self._last_time, time)
        self._times.add(time)

    @property
    def get_last_defined_time(self):
        return -1 if not self._times else max(self._times)

    def append_nop(self, time_slots: int):
        self._last_time += time_slots

    def set_current_qubit(self, qubit: int):
        self._for_qubit = qubit

    @property
    def operations(self):
        return self._operations

    def __str__(self):
        ops = ', '.join([f"{op.get_type_name()}(t={time},op={op})" for time, op in self._operations.items()])
        return f"QuBitOperations<q{self._for_qubit}>[{len(self._operations)}] {{{ops}}}"


class CircuitDefinition:
    def __init__(self, num_qubits: int):
        self._operation_schedules: list[QuBitOperations] = []
        if num_qubits <= 1:
            raise ValueError(f"Inappropriate number of qubits defined '{num_qubits}' but must be >= 1")

        self._operation_schedules = [QuBitOperations(i) for i in range(num_qubits)]

    def __str__(self):
        return f"ScheduleDefinition[{len(self._operation_schedules)}]"

    def add_qubit(self) -> int:
        new_qubit_number = len(self._operation_schedules)
        self._operation_schedules.append(QuBitOperations(new_qubit_number))
        return new_qubit_number

    def remove_qubit(self, qubit_to_be_deleted: int):
        self._validate_qubit(qubit_to_be_deleted)

        being_removed = self._operation_schedules[qubit_to_be_deleted]

        #  unlink multi-operations directly connected to this schedule
        for time, op in being_removed.operations.items():
            if isinstance(op, QuBitOperationMultiParam):
                # IT -> other
                participating_other = op.get_applies_to()
                self._operation_schedules[participating_other].drop_operation(time)
            elif isinstance(op, QuBitOperationMultiParamReference):
                # OTHER -> IT
                participating_other = op.refers_to().get_applied_by()
                self._operation_schedules[participating_other].drop_operation(time)

        # perform renames of remaining nodes
        for qubit in range(qubit_to_be_deleted+1, len(self._operation_schedules)):
            schedule = self._operation_schedules[qubit]
            schedule.set_current_qubit(qubit - 1)

            for op in schedule.operations.values():
                if isinstance(op, QuBitOperationMultiParam):
                    op.set_applied_by(qubit - 1)
                elif isinstance(op, QuBitOperationMultiParamReference):
                    op.refers_to().set_applies_to(qubit - 1)

        # remove the deleted schedule
        self._operation_schedules.pop(qubit_to_be_deleted)

    def set_operation(self, qubit: int, time: int, operation: OperationType) -> QuBitOperationSingleParam:
        """
        Sets operation for qbit number `qbit` at time/index `time`

        :param qubit:         qbit number/index
        :param time:         time at which to define the operation to take place on the qbit
        :param operation:    operation to be applied at time
        """
        self._validate_qubit(qubit)
        CircuitDefinition._validate_time(time)
        (new_op, _) = self._operation_schedules[qubit].add_operation(operation, time)
        return new_op

    def next_operation(self, qubit: int, operation: OperationType) -> None:
        """
        Shorthand for defining operation `operation` to take place for `qbit` in its next available time slot.

        See :func:`base.Definition.setOperation`
        """
        self._validate_qubit(qubit)
        self._operation_schedules[qubit].add_operation(operation)

    def next_nop(self, qubit: int, time_slots: int = 1) -> None:
        """
        Define the next operations for `qbit` to be nothing

        :param qubit:        qbit to schedule empty timeslots for
        :param time_slots:   number of time slots to schedule empty operations for. Default `1` time slot.
        """
        self._validate_qubit(qubit)
        if time_slots < 0:
            raise ValueError(f"Provided timeSlots={time_slots}, but cannot skip negative time slots")

        if time_slots == 0:
            # skip nothing
            return

        self._operation_schedules[qubit].append_nop(time_slots)

    def next_multi_operation(self, qubit: int, qubit_other: int, operation: MultiOperationType) -> None:
        """
        Shorthand for defining operation `operation` to take place for `qbit` in its next available time slot.

        See :func:`base.Definition.setMultiOperation`
        """
        self._validate_qubit(qubit)
        self._validate_qubit(qubit_other)
        CircuitDefinition._validate_multi_qubit_operation(qubit, qubit_other)

        (new_op, time) = self._operation_schedules[qubit].add_multi_operation(operation, qubit_other)
        self._operation_schedules[qubit_other].add_participation(new_op, time)

    def set_multi_operation(self,
                            qubit: int,
                            qubit_other: int,
                            time: int,
                            operation: MultiOperationType) -> QuBitOperationMultiParam:
        """
        Sets operation for qbit number `qbit` at time/index `time`

        :param qubit:         qbit number/index
        :param qubit_other:    other qbit involved in the function
        :param time:         time at which to define the operation to take place on the qbit
        :param operation:    operation to be applied at time
        """
        self._validate_qubit(qubit)
        self._validate_qubit(qubit_other)
        CircuitDefinition._validate_multi_qubit_operation(qubit, qubit_other)
        CircuitDefinition._validate_time(time)

        (new_op, _) = self._operation_schedules[qubit].add_multi_operation(operation, qubit_other, time)
        self._operation_schedules[qubit_other].add_participation(new_op, time)
        return new_op

    def add_some_operation(self, qbit: int, time: int, operation: QuBitOperationBase):
        self._operation_schedules[qbit].add_some_operation(operation, time)

    def drop_operation(self, qbit: int, time: int):
        self._validate_qubit(qbit)
        CircuitDefinition._validate_time(time)

        dropped_op = self._operation_schedules[qbit].drop_operation(time)

        if isinstance(dropped_op, QuBitOperationMultiParam):
            other = dropped_op.get_applies_to()
            self._operation_schedules[other].drop_operation(time)
        elif isinstance(dropped_op, QuBitOperationMultiParamReference):
            other = dropped_op.refers_to().get_applied_by()
            self._operation_schedules[other].drop_operation(time)

    def is_nop(self, qubit: int, time: int):
        self._validate_qubit(qubit)
        CircuitDefinition._validate_time(time)

        return time not in self._operation_schedules[qubit].operations

    def is_multi_target_pair(self, qubit: int, qubit_target: int, time: int):
        self._validate_qubit(qubit)
        CircuitDefinition._validate_time(time)

        if time not in self._operation_schedules[qubit].operations:
            return False

        op = self._operation_schedules[qubit].operations[time]

        return isinstance(op, QuBitOperationMultiParam) and op.get_applies_to() == qubit_target

    def _validate_qubit(self, qbit: int):
        if qbit < 0 or qbit >= self.num_qubits:
            raise ValueError(f"target qbit provided as '{qbit}' but must be >=0 and <{self.num_qubits}")

    @staticmethod
    def _validate_time(time: int):
        if time < 0:
            raise ValueError(f"time must be >= 0, but was {time}")

    @staticmethod
    def _validate_multi_qubit_operation(qbit: int, qbit_other: int):
        if qbit == qbit_other:
            raise ValueError(f"Cannot apply multi-value operation to same qbit {qbit}")

    @property
    def operation_schedules(self):
        return self._operation_schedules

    @property
    def num_qubits(self):
        return len(self._operation_schedules)

    @property
    def max_time(self):
        if self.num_qubits == 0:
            return 0
        return max([item.get_last_defined_time for item in self._operation_schedules])

    @property
    def has_operations(self):
        for s in self._operation_schedules:
            if len(s.operations) > 0:
                return True
        return False

