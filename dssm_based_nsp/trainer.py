import math
from logging import Logger
from typing import List, Tuple

import torch
import torch.nn as nn
from torch.optim.adam import Adam
from torch.utils.data import DataLoader

from dssm_based_nsp.config import TrainConfig
from dssm_based_nsp.model import DSSMModel


class Trainer:
    def __init__(
        self,
        config: TrainConfig,
        model: DSSMModel,
        train_dataloader: DataLoader,
        eval_dataloader: DataLoader,
        logger: Logger,
    ):
        """
        모델을 학습시키기 위한 로직을 관리하는 클래스입니다.
        """
        self.config = config
        self.model = model
        self.train_dataloader = train_dataloader
        self.eval_dataloader = eval_dataloader
        self.logger = logger

        self.device, self.list_ids = self._prepare_device(config.n_gpu, logger)
        self.model.to(self.device)
        if len(self.list_ids) > 1:
            self.model = nn.DataParallel(self.model, device_ids=self.list_ids)
        self.optimizer = Adam(model.parameters(), lr=config.learning_rate)
        self.criterion = nn.CrossEntropyLoss(ignore_index=0)

        self.steps_per_epoch = len(train_dataloader)
        self.total_steps = self.steps_per_epoch * config.epoch

    def train(self):
        self.logger.info("========= Start of train config ========")
        self.logger.info(f"device                : {self.device}")
        self.logger.info(f"dataset length/ train : {len(self.train_dataloader.dataset)}")
        self.logger.info(f"dataset length/ test  : {len(self.eval_dataloader.dataset)}")
        self.logger.info(f"max sequence length   : {self.config.max_seq_len}")
        self.logger.info(f"train batch size      : {self.config.train_batch_size}")
        self.logger.info(f"learning rate         : {self.config.learning_rate}")
        self.logger.info(f"dropout prob          : {self.config.dropout_prob}")
        self.logger.info(f"total epoch           : {self.config.epoch}")
        self.logger.info(f"steps per epoch       : {self.steps_per_epoch}")
        self.logger.info(f"total steps           : {self.total_steps}")
        self.logger.info("========= End of train config ========")
        return

    def _validate(self):
        return

    def _prepare_device(self, n_gpu_use: int, logger: Logger) -> Tuple[torch.device, List[int]]:
        """
        setup GPU device if available, move model into configured device
        """
        n_gpu = torch.cuda.device_count()
        if n_gpu_use > 0 and n_gpu == 0:
            logger.warn("Warning: There's no GPU available on this machine," "training will be performed on CPU.")
            n_gpu_use = 0
        if n_gpu_use > n_gpu:
            logger.warn(
                "Warning: The number of GPU's configured to use is {}, but only {} are available "
                "on this machine.".format(n_gpu_use, n_gpu)
            )
            n_gpu_use = n_gpu
        device = torch.device("cuda:0" if n_gpu_use > 0 else "cpu")
        list_ids = list(range(n_gpu_use))
        return device, list_ids

    def _save_model(self, model: nn.Module, step: int):
        """모델을 지정된 경로에 저장하는 함수입니다."""
        if isinstance(model, nn.DataParallel):
            torch.save(model.module.state_dict(), f"{self.config.save_model_file_prefix}_step_{step}.pth")
        else:
            torch.save(model.state_dict(), f"{self.config.save_model_file_prefix}_step_{step}.pth")