__all__ = ['OnnxClip']

from typing import Optional

import torch
from torch import nn

from onnx2torch.common import OnnxMapping
from onnx2torch.common import OperationConverterResult
from onnx2torch.common import get_const_value
from onnx2torch.common import onnx_mapping_from_node
from onnx2torch.node_converters.registry import add_converter
from onnx2torch.onnx_graph import OnnxGraph
from onnx2torch.onnx_node import OnnxNode


class OnnxClip(nn.Module):

    def __init__(
            self,
            min_val: Optional[torch.Tensor] = None,
            max_val: Optional[torch.Tensor] = None,
    ):
        super().__init__()
        self.min_val = min_val
        self.max_val = max_val

    def forward(self, input_tensor: torch.Tensor) -> torch.Tensor:
        return torch.clamp(input_tensor, self.min_val, self.max_val)


def _create_torch_module(min_val: Optional[torch.Tensor], max_val: Optional[torch.Tensor]) -> nn.Module:
    if min_val is None and max_val is None:
        torch_module = nn.Identity()
    elif min_val == 0 and max_val is None:
        torch_module = nn.ReLU()
    elif min_val == 0 and max_val == 6:
        torch_module = nn.ReLU6()
    else:
        torch_module = OnnxClip(min_val=min_val, max_val=max_val)

    return torch_module


@add_converter(operation_type='Clip', version=11)
@add_converter(operation_type='Clip', version=12)
@add_converter(operation_type='Clip', version=13)
def _(node: OnnxNode, graph: OnnxGraph) -> OperationConverterResult:
    # Min and Max inputs are optional
    min_name = node.input_values[1] if len(node.input_values) > 1 else None
    max_name = node.input_values[2] if len(node.input_values) > 2 else None

    try:
        min_val = get_const_value(min_name, graph) if min_name is not None else None
        max_val = get_const_value(max_name, graph) if max_name is not None else None
    except KeyError:
        raise NotImplementedError('Dynamic value of min/max is not implemented')

    torch_module = _create_torch_module(min_val=min_val, max_val=max_val)

    return OperationConverterResult(
        torch_module=torch_module,
        onnx_mapping=OnnxMapping(
            inputs=(node.input_values[0],),
            outputs=node.output_values,
        ),
    )


@add_converter(operation_type='Clip', version=6)
def _(node: OnnxNode, graph: OnnxGraph) -> OperationConverterResult:   # pylint: disable=unused-argument
    node_attributes = node.attributes
    min_val = node_attributes.get('min', None)
    max_val = node_attributes.get('max', None)

    torch_module = _create_torch_module(
        min_val=torch.tensor(min_val) if min_val is not None else None,
        max_val=torch.tensor(max_val) if max_val is not None else None,
    )

    return OperationConverterResult(
        torch_module=torch_module,
        onnx_mapping=onnx_mapping_from_node(node),
    )
