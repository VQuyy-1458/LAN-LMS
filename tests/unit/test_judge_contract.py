import pytest
from judge.comparators.output import compare
from judge.runners.container import DockerJudge, TestCase
from judge.limits import Limits


def test_comparators_preserve_internal_whitespace():
    assert compare(b" a  b \r\n", b" a  b\n", "normalized")
    assert not compare(b"a b", b"ab", "normalized")
    assert not compare(b"5\r\n", b"5\n", "exact")


@pytest.mark.parametrize("name", ["../secret", "/root", "C:foo", "..", "stdout"])
def test_unsafe_file_config_is_rejected_before_docker(name):
    with pytest.raises(ValueError):
        DockerJudge().grade(
            "int main(){}", "c", [TestCase(b"", b"")], input_filename=name
        )


def test_limits_are_validated():
    with pytest.raises(ValueError):
        Limits(time_ms=0).validate()
