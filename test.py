"""
Model testing entrypoint.
"""

import os

from mindspore import context
from mindspore.common import set_seed
from mindspore.nn.loss import SoftmaxCrossEntropyWithLogits
from mindspore.train.model import Model
from mindspore.train.serialization import load_checkpoint
from mindspore.train.serialization import load_param_into_net

from src.config import Config
from src.dataset.cifar10 import create_cifar10_dataset
from src.dataset.svhn_dataset import create_svhn_dataset
from src.network import WRN
from src.utils import init_utils

if __name__ == '__main__':
    conf = Config(training=False)
    init_utils(conf)
    set_seed(conf.seed)

    # Initialize context
    try:
        device_id = int(os.getenv('DEVICE_ID'))
    except TypeError:
        device_id = 0
    context.set_context(
        mode=context.GRAPH_MODE,
        device_target=conf.device_target,
        save_graphs=False,
        device_id=device_id,
    )

    # Create dataset
    if conf.dataset == 'cifar10':
        dataset = create_cifar10_dataset(
            dataset_path=conf.dataset_path,
            do_train=False,
            repeat_num=1,
            batch_size=conf.batch_size,
            target=conf.device_target,
        )
    elif conf.dataset == 'svhn':
        dataset = create_svhn_dataset(
            dataset_path=conf.dataset_path,
            do_train=False,
            repeat_num=1,
            batch_size=conf.batch_size,
            target=conf.device_target,
        )
    else:
        raise ValueError("Dataset unsupported.(Choose from ['cifar10', 'svhn'])")

    step_size = dataset.get_dataset_size()

    # Define net
    net = WRN(160, 3, conf.class_num)

    # Load checkpoint
    param_dict = load_checkpoint(conf.checkpoint_path)
    load_param_into_net(net, param_dict)
    net.set_train(False)

    # Define loss and model
    loss = SoftmaxCrossEntropyWithLogits(sparse=True, reduction='mean')
    model = Model(net, loss_fn=loss, metrics={
        'top_1_accuracy', 'top_5_accuracy',
    })

    # Eval model
    res = model.eval(dataset)
    print('result:', res, 'checkpoint:', conf.checkpoint_path)
