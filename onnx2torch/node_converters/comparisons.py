__all__ = ['OnnxCompare']

import torch
from torch import nn

from onnx2torch.common import OperationConverterResult
from onnx2torch.common import onnx_mapping_from_node
from onnx2torch.node_converters.registry import add_converter
from onnx2torch.onnx_graph import OnnxGraph
from onnx2torch.onnx_node import OnnxNode

_TORCH_FUNCTION_FROM_ONNX_TYPE = {
    'Equal': torch.eq,
    'Less': torch.less,
    'LessOrEqual': torch.less_equal,
    'Greater': torch.greater,
    'GreaterOrEqual': torch.greater_equal,
}


class OnnxCompare(nn.Module):

    def __init__(self, operation_type: str):
        super().__init__()
        self.compare_function = _TORCH_FUNCTION_FROM_ONNX_TYPE[operation_type]

    def forward(self, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        return self.compare_function(a, b)


@add_converter(operation_type='Equal', version=7)
@add_converter(operation_type='Equal', version=11)
@add_converter(operation_type='Equal', version=13)
@add_converter(operation_type='Less', version=7)
@add_converter(operation_type='Less', version=9)
@add_converter(operation_type='Less', version=13)
@add_converter(operation_type='Greater', version=7)
@add_converter(operation_type='Greater', version=9)
@add_converter(operation_type='Greater', version=13)
@add_converter(operation_type='LessOrEqual', version=12)
@add_converter(operation_type='GreaterOrEqual', version=12)
def _(node: OnnxNode, graph: OnnxGraph) -> OperationConverterResult:  # pylint: disable=unused-argument
    return OperationConverterResult(
        torch_module=OnnxCompare(operation_type=node.operation_type),
        onnx_mapping=onnx_mapping_from_node(node=node),
    )
