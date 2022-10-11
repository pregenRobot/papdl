
from papdl.loader import Loader


def test_loader():
    l = Loader("test path")
    assert l.model_path == "test path"