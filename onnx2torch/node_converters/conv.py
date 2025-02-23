__all__ = []

import torch
from torch import nn

from onnx2torch.common import OnnxMapping
from onnx2torch.common import OperationConverterResult
from onnx2torch.node_converters.registry import add_converter
from onnx2torch.onnx_graph import OnnxGraph
from onnx2torch.onnx_node import OnnxNode

_CONV_CLASS_FROM_SPATIAL_RANK = {
    1: nn.Conv1d,
    2: nn.Conv2d,
    3: nn.Conv3d,
}


@add_converter(operation_type='Conv', version=1)
@add_converter(operation_type='Conv', version=11)
def _(node: OnnxNode, graph: OnnxGraph) -> OperationConverterResult:
    weights_value_name = node.input_values[1]
    weights = graph.initializers[weights_value_name]
    weights = weights.to_torch()
    if len(node.input_values) == 3:
        bias_value_name = node.input_values[2]
        bias = graph.initializers[bias_value_name]
        bias = bias.to_torch()
    else:
        bias = None

    spatial_rank = len(weights.shape) - 2
    conv_class = _CONV_CLASS_FROM_SPATIAL_RANK.get(spatial_rank, None)
    if conv_class is None:
        raise NotImplementedError(f'Convolution operation with spatial rank == {spatial_rank} is not implemented')

    node_attributes = node.attributes
    kernel_size = node_attributes.get('kernel_shape', weights.shape[2:])
    stride = node_attributes.get('strides', 1)
    padding = node_attributes.get('pads', [0]*4)
    dilation = node_attributes.get('dilations', 1)
    groups = node_attributes.get('group', 1)

    out_channels = weights.shape[0]
    in_channels = weights.shape[1]*groups

    auto_pad = node_attributes.get('auto_pad', 'NOTSET')
    if auto_pad == 'NOTSET':
        half_len = len(padding) // 2
        if tuple(padding[:half_len]) != tuple(padding[half_len:]):
            raise NotImplementedError(f'Only symmetric padding is implemented ({padding})')

        padding = padding[:half_len]
    elif auto_pad in ('SAME_UPPER', 'SAME_LOWER', 'VALID'):
        raise NotImplementedError(f'"{auto_pad}" auto_pad is not implemented')
    else:
        raise ValueError(f'Got unexpected auto_pad value "{auto_pad}"')

    torch_module = conv_class(
        in_channels=in_channels,
        out_channels=out_channels,
        kernel_size=kernel_size,
        stride=stride,
        padding=padding,
        dilation=dilation,
        groups=groups,
        bias=bias is not None,
    )

    with torch.no_grad():
        torch_module.weight.data = weights
        if bias is not None:
            torch_module.bias.data = bias

    return OperationConverterResult(
        torch_module=torch_module,
        onnx_mapping=OnnxMapping(
            inputs=(node.input_values[0],),
            outputs=node.output_values,
        ),
    )
