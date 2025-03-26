
from base.models import CircuitDefinition, OperationType, QuBitOperationSingleParam


class ValidationResult:
    def __init__(self, success: bool, message: str | None) -> None:
        self.success = success
        self.message = message

    @staticmethod
    def failure(message : str):
        return ValidationResult(False, message)

    @staticmethod
    def ok():
        return ValidationResult(True, None)

class UIExecutionValidator:
    @staticmethod
    def can_evaluate(circuit : CircuitDefinition) -> ValidationResult:
        # the messages could be expanded to provide more details on what went wrong.
        # the main idea is that we could probably expand the UI to allow multiple measuring operations in the future, among other things
        # the current setup is actually a bit limiting. e.g. 
        # another useful setup might implicitly measuring all qubits if there's no measures at all defined in the circuit.
        
        if not circuit.has_operations:
            return ValidationResult.failure("Circuit does not contain any gates; nothing to evaluate")
        
        if not UIExecutionValidator._validate_is_all_measure_at_last(circuit):
            return ValidationResult.failure("Final gate in circuit was not a measure gate. Ensure at least one measure gate is placed at the end of the circuit to evaluate the associated qubit")
        
        if not UIExecutionValidator._validate_has_no_measure_before_last(circuit):
            return ValidationResult.failure("Only one computational basis measuring time is currently supported, and this measuring must take place at the very end of the circuit timeline. If multiple qubits must be measured, ensure their measure gates are placed at the same time")
        
        return ValidationResult.ok()
    
    @staticmethod
    def _validate_is_all_measure_at_last(circuit: CircuitDefinition):
        last_operation_time = circuit.max_time
        for qubit in circuit.operation_schedules:
            if last_operation_time in qubit.operations:
                op = qubit.operations[last_operation_time]
                if not isinstance(op, QuBitOperationSingleParam) or op.get_type() != OperationType.MEASURE:
                    return False
        return True
    
    @staticmethod
    def _validate_has_no_measure_before_last(circuit: CircuitDefinition):
        last_operation_time = circuit.max_time
        for qubit in circuit.operation_schedules:
            for time, op in qubit.operations.items():
                if time == last_operation_time: 
                    continue
                if isinstance(op, QuBitOperationSingleParam) and op.get_type() == OperationType.MEASURE:
                    return False
        return True