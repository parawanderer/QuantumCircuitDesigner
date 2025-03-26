import math
import unittest

from parameterized import parameterized

from base.models import CircuitDefinition, OperationType, MultiOperationType, QuBitOperationMultiParam, \
    QuBitOperationSingleParam, QuBitOperations, QuBitOperationMultiParamReference


class BuildDefinitionTest(unittest.TestCase):
    def _buildTestDefinition(self):
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

        return d

    def _assertCorrectTemplate(self, d):
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

    def test_build_with_next(self):
        d = self._buildTestDefinition()
        self._assertCorrectTemplate(d)

    def test_build_with_set(self):
        d = CircuitDefinition(3)

        # t = 0
        d.set_operation(0, 0, OperationType.H)
        # t = 1
        d.set_operation(1, 1, OperationType.X)
        # t = 2
        d.set_multi_operation(0, 1, 2, MultiOperationType.CNOT)
        # t = 3
        d.set_multi_operation(2, 0, 3, MultiOperationType.CNOT)
        # t = 4
        d.set_operation(0, 4, OperationType.MEASURE)
        d.set_operation(1, 4, OperationType.MEASURE)
        d.set_operation(2, 4, OperationType.MEASURE)

        self._assertCorrectTemplate(d)

    def test_build_with_set_out_of_order(self):
        d = CircuitDefinition(3)

        # t = 3
        d.set_multi_operation(2, 0, 3, MultiOperationType.CNOT)

        # t = 4
        d.set_operation(0, 4, OperationType.MEASURE)
        d.set_operation(1, 4, OperationType.MEASURE)
        d.set_operation(2, 4, OperationType.MEASURE)

        # t = 0
        d.set_operation(0, 0, OperationType.H)

        # t = 2
        d.set_multi_operation(0, 1, 2, MultiOperationType.CNOT)

        # t = 1
        d.set_operation(1, 1, OperationType.X)

        self._assertCorrectTemplate(d)

    def test_stringify(self):
        stringified = str(self._buildTestDefinition())
        self.assertIsNotNone(stringified)

    @parameterized.expand([
        [-5],
        [-1],
        [0],
        [1]
    ])
    def test_init_throws_when_too_few_qbits(self, init_qbits):
        self.assertRaises(ValueError, lambda: CircuitDefinition(init_qbits))

    @parameterized.expand([
        [-5],
        [-1],
    ])
    def test_set_operation_throws_when_bad_time(self, time):
        d = CircuitDefinition(5)
        self.assertRaises(ValueError, lambda: d.set_operation(0, time, OperationType.MEASURE))

    @parameterized.expand([
        [-5],
        [-1],
        [6],
        [10]
    ])
    def test_set_operation_throws_when_bad_qbit(self, qbit):
        d = CircuitDefinition(5)
        self.assertRaises(ValueError, lambda: d.set_operation(qbit, 1, OperationType.MEASURE))

    @parameterized.expand([
        [-5],
        [-1],
        [6],
        [10]
    ])
    def test_next_operation_throws_when_bad_qbit(self, qbit):
        d = CircuitDefinition(5)
        self.assertRaises(ValueError, lambda: d.next_operation(qbit, OperationType.MEASURE))

    @parameterized.expand([
        [-5, 0],
        [-1, 0],
        [6, 0],
        [10, 0],
        [0, -5],
        [0, -1],
        [0, 6],
        [0, 10],
        [-1, -1],
        [10, 10]
    ])
    def test_set_multi_operation_throws_when_bad_qbit(self, qbit, other_qbit):
        d = CircuitDefinition(5)
        self.assertRaises(ValueError, lambda: d.set_multi_operation(qbit, other_qbit, 1, MultiOperationType.CNOT))

    @parameterized.expand([
        [0, 0],
        [1, 1],
        [2, 2],
        [3, 3],
        [4, 4],
    ])
    def test_set_multi_operation_throws_when_other_equals_self(self, qbit, other_qbit):
        d = CircuitDefinition(5)
        self.assertRaises(ValueError, lambda: d.set_multi_operation(qbit, other_qbit, 1, MultiOperationType.CNOT))

    @parameterized.expand([
        [0],
        [1],
        [2],
        [5],
        [10],
        [100]
    ])
    def test_set_nop(self, time_slots: int):
        d = CircuitDefinition(5)
        d.next_nop(0, time_slots)
        # works, no error thrown

    @parameterized.expand([
        [-1],
        [-5],
        [-10],
        [-100]
    ])
    def test_set_nop_throws_when_invalid_skip(self, time_slots: int):
        d = CircuitDefinition(5)
        self.assertRaises(ValueError, lambda: d.next_nop(0, time_slots))


class QBitOperationsTest(unittest.TestCase):
    def test_to_string(self):
        op = QuBitOperations(0)
        op.add_operation(OperationType.H, 1)
        op.add_multi_operation(MultiOperationType.CNOT, 1, 2)
        self.assertIsNotNone(str(op))

if __name__ == '__main__':
    unittest.main()
