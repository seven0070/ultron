"""Model-layer exceptions."""


class ModelError(Exception):
    pass


class ModelNotFoundError(ModelError):
    pass


class ModelLoadError(ModelError):
    pass


class ModelFileMissingError(ModelError):
    pass
