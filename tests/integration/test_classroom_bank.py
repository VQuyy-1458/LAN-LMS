"""Compile and execute every original classroom reference against all its cases."""
import os
import pytest
from demo.classroom_problems import bank
from judge.runners.container import DockerJudge, TestCase
from judge.limits import Limits

QUESTIONS=[question for group in bank().values() for question in group]


@pytest.mark.skipif(os.getenv("RUN_DOCKER_TESTS")!="1",reason="Real Docker required")
@pytest.mark.parametrize("question",QUESTIONS,ids=[question.code for question in QUESTIONS])
def test_reference_question_bank(question):
    result=DockerJudge().grade(question.solution,"cpp",
        [TestCase(inp.encode(),out.encode(),100/len(question.cases)) for inp,out in question.cases],
        Limits(time_ms=2000,memory_mib=512),comparator="normalized",io_mode=question.io_mode,
        input_filename=question.input_filename or "input.txt",output_filename=question.output_filename or "output.txt")
    assert result.verdict=="Accepted",(question.code,result)
