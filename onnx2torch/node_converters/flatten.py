import torch
from torch import nn

from onnx2torch.common import OperationConverterResult
from onnx2torch.common import onnx_mapping_from_node
from onnx2torch.node_converters.registry import add_converter
from onnx2torch.onnx_graph import OnnxGraph
from onnx2torch.onnx_node import OnnxNode
import numpy as np


class OnnxFlatten(nn.Module):

    def __init__(self, axis: int = 1):
        super().__init__()
        self.axis = axis

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = torch.flatten(x, end_dim=self.axis - 1)
        return torch.flatten(x, start_dim=1)

    @classmethod
    def maybe_create_simple_linear(cls, axis: int = 1):
        if axis == 1:
            return nn.Flatten(start_dim=axis)
        else:
            cls(axis=axis)


@add_converter(operation_type='Flatten', version=13)
@add_converter(operation_type='Flatten', version=11)
@add_converter(operation_type='Flatten', version=9)
def _(node: OnnxNode, graph: OnnxGraph) -> OperationConverterResult:   # pylint: disable=unused-argument
    axis = node.attributes.get('axis', 1)
    torch_module = OnnxFlatten(
        axis=axis,
    )

    return OperationConverterResult(
        torch_module=torch_module,
        onnx_mapping=onnx_mapping_from_node(node=node),
    )
