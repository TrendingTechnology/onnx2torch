__all__ = ['OnnxWhere']

import torch
from torch import nn

from onnx2torch.common import OperationConverterResult
from onnx2torch.common import onnx_mapping_from_node
from onnx2torch.node_converters.registry import add_converter
from onnx2torch.onnx_graph import OnnxGraph
from onnx2torch.onnx_node import OnnxNode


class OnnxWhere(nn.Module):

    def forward(self, condition: torch.Tensor, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        return torch.where(condition, x, y)


@add_converter(operation_type='Where', version=9)
@add_converter(operation_type='Where', version=16)
def _(node: OnnxNode, graph: OnnxGraph) -> OperationConverterResult:  # pylint: disable=unused-argument
    return OperationConverterResult(
        torch_module=OnnxWhere(),
        onnx_mapping=onnx_mapping_from_node(node=node),
    )
