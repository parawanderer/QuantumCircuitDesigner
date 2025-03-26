import json
import unittest

from base.models import CircuitDefinition, OperationType, MultiOperationType, QuBitOperations, \
    QuBitOperationMultiParamReference, QuBitOperationSingleParam, QuBitOperationMultiParam
from base.serialization import JsonSerializer, JsonDeserializer

EXAMPLE_JSON = {
        "version": "0.0.1",
        "definition": [
            {
                "qubit": 0,
                "schedule": [
                    {
                        "time": 0,
                        "operation": "H"
                    },
                    {
                        "time": 2,
                        "operation": "CNOT",
                        "params": {
                            "appliesTo": 1
                        }
                    },
                    {
                        "time": 4,
                        "operation": "MEASURE"
                    }
                ]
            },
            {
                "qubit": 1,
                "schedule": [
                    {
                        "time": 1,
                        "operation": "RX"
                    },
                    {
                        "time": 4,
                        "operation": "MEASURE"
                    }
                ]
            },
            {
                "qubit": 2,
                "schedule": [
                    {
                        "time": 3,
                        "operation": "CNOT",
                        "params": {
                            "appliesTo": 0
                        }
                    },
                    {
                        "time": 4,
                        "operation": "MEASURE"
                    }
                ]
            }
        ]
    }

class TestSerialization(unittest.TestCase):

    def test_json_serialization(self):
        d = CircuitDefinition(3)

        # t = 0
        d.next_operation(0, OperationType.H)
        d.next_nop(1)
        d.next_nop(2)

        # t = 1
        d.next_nop(0)
        d.next_operation(1, OperationType.X)
        d.next_nop(2)

        # t = 2
        d.next_multi_operation(0, 1, MultiOperationType.CNOT)
        d.next_nop(2)

        # t = 3
        d.next_nop(1)
        d.next_multi_operation(2, 0, MultiOperationType.CNOT)

        # t = 4
        d.next_operation(0, OperationType.MEASURE)
        d.next_operation(1, OperationType.MEASURE)
        d.next_operation(2, OperationType.MEASURE)

        json_result = JsonSerializer.convert(d)

        self.assertEqual(json.loads(json_result), EXAMPLE_JSON)


class TestDeserialization(unittest.TestCase):

    def test_json_deserialization(self):
        json_string = json.dumps(EXAMPLE_JSON)
        d = JsonDeserializer.parse(json_string)

        self.assertIsNotNone(d.operation_schedules)
        self.assertEqual(3, d.num_qubits)
        self.assertEqual(3, len(d.operation_schedules))

        # q0 schedule
        schedule_wrapper_0 = d.operation_schedules[0]
        self.assertIsNotNone(schedule_wrapper_0)
        self.assertEqual(4, len(schedule_wrapper_0.operations))

        self._assertOperationSingleParam(schedule_wrapper_0, OperationType.H, 0)
        self._assertOperationMultiParam(schedule_wrapper_0, MultiOperationType.CNOT, 2, 1)
        self._assertMultiParamReferenceTo(schedule_wrapper_0, MultiOperationType.CNOT, 3)
        self._assertOperationSingleParam(schedule_wrapper_0, OperationType.MEASURE, 4)

        # q1 schedule
        schedule_wrapper_1 = d.operation_schedules[1]
        self.assertIsNotNone(schedule_wrapper_1)
        self.assertEqual(3, len(schedule_wrapper_1.operations))

        self._assertOperationSingleParam(schedule_wrapper_1, OperationType.X, 1)
        self._assertMultiParamReferenceTo(schedule_wrapper_1, MultiOperationType.CNOT, 2)
        self._assertOperationSingleParam(schedule_wrapper_1, OperationType.MEASURE, 4)

        # q2 schedule
        schedule_wrapper_2 = d.operation_schedules[2]
        self.assertIsNotNone(schedule_wrapper_2)
        self.assertEqual(2, len(schedule_wrapper_2.operations))

        self._assertOperationMultiParam(schedule_wrapper_2, MultiOperationType.CNOT, 3, 0)
        self._assertOperationSingleParam(schedule_wrapper_2, OperationType.MEASURE, 4)

    def _assertMultiParamReferenceTo(self, wrapper: QuBitOperations, operation: MultiOperationType, time: int):
        self.assertTrue(time in wrapper.operations)
        self.assertEqual(operation.name, wrapper.operations[time].get_type_name())
        self.assertIsInstance(wrapper.operations[time], QuBitOperationMultiParamReference)
        self.assertIsNotNone(wrapper.operations[time].refers_to())

    def _assertOperationSingleParam(self, wrapper: QuBitOperations, operation: OperationType, time: int):
        self.assertTrue(time in wrapper.operations)
        self.assertEqual(operation.name, wrapper.operations[time].get_type_name())
        self.assertIsInstance(wrapper.operations[time], QuBitOperationSingleParam)
        self.assertEqual(operation, wrapper.operations[time].get_type())

    def _assertOperationMultiParam(self, wrapper: QuBitOperations, operation: MultiOperationType, time: int, other_qbit: int):
        self.assertTrue(time in wrapper.operations)
        self.assertEqual(operation.name, wrapper.operations[time].get_type_name())
        self.assertIsInstance(wrapper.operations[time], QuBitOperationMultiParam)
        self.assertEqual(operation, wrapper.operations[time].get_type())
        self.assertEqual(other_qbit, wrapper.operations[time].get_applies_to())


if __name__ == '__main__':
    unittest.main()
