import json
from typing import Any

from base.models import DefinitionVisitor, CircuitDefinition, QuBitOperationSingleParam, QuBitOperationMultiParam, \
    QuBitOperations, QuBitOperationMultiParamReference, OperationType, MultiOperationType


class JsonParsingError(RuntimeError):
    pass


class DefinitionJsonConvertorVisitor(DefinitionVisitor):
    VERSION = "0.0.1"

    def __init__(self, d: CircuitDefinition):
        self._d = d

    def handle_single_param_op(self, op: QuBitOperationSingleParam):
        return {
            "time": -1,
            "operation": op.get_type().name,
        }

    def handle_multi_param_op(self, op: QuBitOperationMultiParam):
        return {
            "time": -1,
            "operation": op.get_type().name,
            "params": {
                "appliesTo": op.get_applies_to()
            }
        }

    def handle_multi_param_ref(self, op: QuBitOperationMultiParamReference) -> Any:
        # is not serialized
        return None

    def convert_schedule_items(self, schedule_item: QuBitOperations):
        scheduled_operations = []
        for time, operation in schedule_item.operations.items():
            converted_dict = operation.accept(self)
            if converted_dict is not None:
                converted_dict["time"] = time
                scheduled_operations.append(converted_dict)
        scheduled_operations.sort(key=lambda op: op["time"])
        return scheduled_operations

    def convert_schedule(self):
        items = []
        for qbit, qbitSchedule in enumerate(self._d.operation_schedules):
            items.append({
                "qubit": qbit,
                "schedule": self.convert_schedule_items(qbitSchedule)
            })
        return items

    def to_json(self) -> str:
        schedule_items = self.convert_schedule()

        json_obj = {
            "version": DefinitionJsonConvertorVisitor.VERSION,
            "definition": schedule_items
        }
        return json.dumps(json_obj)

    @staticmethod
    def convert(d: CircuitDefinition) -> str:
        return DefinitionJsonConvertorVisitor(d).to_json()


class DefinitionJsonParser:
    VERSION = "0.0.1"

    SINGLE_OP_MAPPER = {v.name: v for v in OperationType}

    MULTI_OP_MAPPER = {v.name: v for v in MultiOperationType}

    def __init__(self, source: any):
        self._source = source

    def parse(self):
        return self._parse_with_validations(self._source)

    def _parse_with_validations(self, source: any) -> CircuitDefinition:
        if not isinstance(source, dict):
            raise JsonParsingError(f"Expected top level json object but got {type(source)}")

        if "version" not in source:
            raise JsonParsingError(f"Expected to see field 'version' in top level of json but field was missing")

        if source["version"] != DefinitionJsonParser.VERSION:
            raise JsonParsingError(f"Expected version as '{DefinitionJsonParser.VERSION}' but got '{source['version']}'")

        if "definition" not in source:
            raise JsonParsingError(f"Expected to see field 'definition' in top level of json but field was missing")

        definition = source["definition"]

        if not isinstance(definition, list):
            raise JsonParsingError(f"Required to see field 'definition' to be a list but got {type(source['definition'])}")

        if len(definition) == 0:
            raise JsonParsingError(f"Expected 'definition' to contain at least one definition")

        # top level is ok
        schedule: CircuitDefinition = CircuitDefinition(len(definition))
        self._try_parse_items(schedule, definition)

        return schedule

    def _try_parse_items(self, schedule: CircuitDefinition, items: list[any]):
        qubit_count = len(items)
        expected_qubits = set([i for i in range(len(items))])

        for i in range(len(items)):
            item = items[i]
            if not isinstance(item, dict):
                raise JsonParsingError(f"Expected dictionary at json path 'definitions[{i}]' but got {type(item)}")

            if "qubit" not in item:
                raise JsonParsingError(f"Expected 'qubit' at json path 'definitions[{i}].qubit' but field was missing")

            qubit = item["qubit"]
            if not isinstance(qubit, int):
                raise JsonParsingError(f"Expected 'qubit' at json path 'definitions[{i}].qubit' to be an integer but was: {qubit}")

            if qubit < 0 or qubit >= qubit_count:
                raise JsonParsingError(f"Only qubits '0' through '{qubit_count-1}' are expected for this definition, but got qubit {qubit} at json path 'definitions[{i}]")

            if qubit not in expected_qubits:
                raise JsonParsingError(f"Found a duplicate definition for qubit '{qubit}' at json path 'definitions[{i}]")
            expected_qubits.remove(qubit)

            if "schedule" not in item:
                raise JsonParsingError(f"Expected 'schedule' at json path 'definitions[{i}].schedule' but field was missing")

            item_schedule = item["schedule"]
            if not isinstance(item_schedule, list):
                raise JsonParsingError(f"Expected 'schedule' at json path 'definitions[{i}].schedule' to be a list but got {type(schedule)}")

            for j, item in enumerate(item_schedule):
                self._try_parse_operation(schedule, item, i, j, qubit)

    def _try_parse_operation(self, schedule: CircuitDefinition, item: any, i: int, j: int, qubit: int) -> None:
        if not isinstance(item, dict):
            raise JsonParsingError(f"Expected to see a dictionary at json path 'definitions[{i}].schedule[{j}]' but got {type(item)}")

        if "time" not in item:
            raise JsonParsingError(f"Expected to see field 'time' at json path 'definitions[{i}].schedule[{j}].time' but field was missing")

        time = item["time"]
        if not isinstance(time, int):
            raise JsonParsingError(f"Expected to see integer field 'time' at json path 'definitions[{i}].schedule[{j}].time' but was {type(time)}")

        if time < 0:
            raise JsonParsingError(f"Expected field 'time' to be greater than 0 at json path 'definitions[{i}].schedule[{j}].time' but was {time}")

        if "operation" not in item:
            raise JsonParsingError(f"Expected to see field 'operation' at json path 'definitions[{i}].schedule[{j}].operation' but field was missing")

        operation = item["operation"]
        if not isinstance(operation, str):
            raise JsonParsingError(f"Expected to see string field 'operation' at json path 'definitions[{i}].schedule[{j}].operation' but was {type(operation)}")

        if len(operation) == 0:
            raise JsonParsingError(f"Found empty operation at json path 'definitions[{i}].schedule[{j}].operation'")

        if operation in DefinitionJsonParser.SINGLE_OP_MAPPER:
            self._try_map_single_operation(schedule, qubit, time, DefinitionJsonParser.SINGLE_OP_MAPPER[operation])
        elif operation in DefinitionJsonParser.MULTI_OP_MAPPER:
            self._try_map_multi_operations(schedule, qubit, time, item, DefinitionJsonParser.MULTI_OP_MAPPER[operation], i, j)
        else:
            raise JsonParsingError(f"Found unexpected operation at json path 'definitions[{i}].schedule[{j}].operation' with value '{operation}'")

    def _try_map_single_operation(self,
                                  schedule: CircuitDefinition,
                                  qubit: int,
                                  time: int,
                                  operation: OperationType) -> None:
        schedule.set_operation(qubit, time, operation)

    def _try_map_multi_operations(self,
                                  schedule: CircuitDefinition,
                                  qubit: int,
                                  time: int,
                                  item: dict,
                                  operation: MultiOperationType,
                                  i: int,
                                  j: int) -> None:
        qubits_count = schedule.num_qubits

        if "params" not in item:
            raise JsonParsingError(f"Expected to find params at json path 'definitions[{i}].schedule[{j}].operation.params' but field was missing")

        params = item["params"]
        if not isinstance(params, dict):
            raise JsonParsingError(f"Expected to find object at json path 'definitions[{i}].schedule[{j}].operation.params' but was {type(params)}")

        if "appliesTo" not in params:
            raise JsonParsingError(f"Expected to find field 'appliesTo' at 'definitions[{i}].schedule[{j}].operation.params.appliesTo' but field was missing")

        applies_to = params["appliesTo"]
        if not isinstance(applies_to, int):
            raise JsonParsingError(f"Expected field 'appliesTo' to be integer at json path 'definitions[{i}].schedule[{j}].operation.params.appliesTo' but was {type(applies_to)}")

        if applies_to < 0 or applies_to >= qubits_count:
            raise JsonParsingError(f"Expected field 'appliesTo' to be a valid number between 0 and {qubits_count-1} but was {applies_to}")

        schedule.set_multi_operation(qubit, applies_to, time, operation)


class JsonSerializer:
    @staticmethod
    def convert(d: CircuitDefinition) -> str:
        return DefinitionJsonConvertorVisitor.convert(d)


class JsonDeserializer:
    @staticmethod
    def parse(json_str: str) -> CircuitDefinition:
        json_map = json.loads(json_str)
        return DefinitionJsonParser(json_map).parse()

