from typing import Any, Callable, Dict


async def execute_operation(
    execution_context: "ExecutionContext",
    error_coercer: Callable[[Exception], dict],
) -> Dict[str, Any]:
    operation = execution_context.operation
    operation_type = execution_context.schema.find_type(
        execution_context.schema.get_operation_type(
            operation.operation.capitalize()
        )
    )

    print(
        ">> execute_operation",
        {
            "operation": operation,
            # "operation_type": operation_type,
            "allow_paralellization": operation.allow_parallelization,
        },
    )

    data = await operation.selection_set(
        execution_context,
        operation_type,
        execution_context.root_value,
        allow_parallelization=operation.allow_parallelization,
    )

    print({"result": data})
