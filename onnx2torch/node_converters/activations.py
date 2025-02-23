__all__ = ['OnnxExp']

import torch
from torch import nn

from onnx2torch.common import OperationConverterResult
from onnx2torch.common import onnx_mapping_from_node
from onnx2torch.node_converters.registry import add_converter
from onnx2torch.onnx_graph import OnnxGraph
from onnx2torch.onnx_node import OnnxNode


class OnnxExp(nn.Module):

    def forward(self, input_tensor: torch.Tensor) -> torch.Tensor:
        return torch.exp(input_tensor)


class OnnxSoftmaxV1V11(nn.Module):
    def __init__(self, axis: int = 1):
        super().__init__()
        self.axis = axis

    def forward(self, input_tensor: torch.Tensor) -> torch.Tensor:
        shape = input_tensor.shape
        result = torch.flatten(input_tensor, start_dim=self.axis)
        result = torch.softmax(result, -1)

        return torch.reshape(result, shape)


@add_converter(operation_type='Softmax', version=1)
@add_converter(operation_type='Softmax', version=11)
def _(node: OnnxNode, graph: OnnxGraph) -> OperationConverterResult:  # pylint: disable=unused-argument
    return OperationConverterResult(
        torch_module=OnnxSoftmaxV1V11(axis=node.attributes.get('axis', 1)),
        onnx_mapping=onnx_mapping_from_node(node=node),
    )


@add_converter(operation_type='Softmax', version=13)
def _(node: OnnxNode, graph: OnnxGraph) -> OperationConverterResult:  # pylint: disable=unused-argument
    axis = node.attributes.get('axis', -1)

    return OperationConverterResult(
        torch_module=torch.nn.Softmax(dim=axis),
        onnx_mapping=onnx_mapping_from_node(node=node),
    )


@add_converter(operation_type='Sigmoid', version=1)
@add_converter(operation_type='Sigmoid', version=6)
@add_converter(operation_type='Sigmoid', version=13)
def _(node: OnnxNode, graph: OnnxGraph) -> OperationConverterResult:  # pylint: disable=unused-argument

    return OperationConverterResult(
        torch_module=nn.Sigmoid(),
        onnx_mapping=onnx_mapping_from_node(node=node),
    )


@add_converter(operation_type='Relu', version=6)
@add_converter(operation_type='Relu', version=13)
@add_converter(operation_type='Relu', version=14)
def _(node: OnnxNode, graph: OnnxGraph) -> OperationConverterResult:   # pylint: disable=unused-argument
    return OperationConverterResult(
        torch_module=nn.ReLU(),
        onnx_mapping=onnx_mapping_from_node(node=node),
    )


@add_converter(operation_type='Exp', version=6)
@add_converter(operation_type='Exp', version=13)
def _(node: OnnxNode, graph: OnnxGraph) -> OperationConverterResult:  # pylint: disable=unused-argument
    return OperationConverterResult(
        torch_module=OnnxExp(),
        onnx_mapping=onnx_mapping_from_node(node=node),
    )
