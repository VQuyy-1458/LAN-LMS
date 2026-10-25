"""Real Docker tests. Explicitly opt in; never fall back to executing student code on host."""

import os
import pytest
from judge.runners.container import DockerJudge, TestCase
from judge.limits import Limits

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DOCKER_TESTS") != "1",
    reason="Set RUN_DOCKER_TESTS=1 after building judge image",
)

SOURCES = {
    "c": '#include <stdio.h>\nint main(){int a,b;scanf("%d%d",&a,&b);printf("%d\\n",a+b);}',
    "cpp": '#include <iostream>\nint main(){int a,b;std::cin>>a>>b;std::cout<<a+b<<"\\n";}',
    "java": "import java.util.*; public class Main {public static void main(String[] a){Scanner s=new Scanner(System.in);System.out.println(s.nextInt()+s.nextInt());}}",
}


@pytest.mark.parametrize("language", ["c", "cpp", "java"])
def test_stdio_three_languages(language):
    r = DockerJudge().grade(
        SOURCES[language],
        language,
        [TestCase(b"2 3", b"5\n", 10)],
        limits=Limits(memory_mib=512),
    )
    assert r.verdict == "Accepted" and r.score == 10, r


@pytest.mark.parametrize("language", ["c", "cpp", "java"])
def test_file_io_three_languages(language):
    sources = {
        "c": '#include <stdio.h>\nint main(){int a,b;FILE*i=fopen("input.txt","r"),*o=fopen("output.txt","w");fscanf(i,"%d%d",&a,&b);fprintf(o,"%d",a+b);fclose(o);}',
        "cpp": '#include <fstream>\nint main(){int a,b;std::ifstream i("input.txt");std::ofstream o("output.txt");i>>a>>b;o<<a+b;}',
        "java": 'import java.io.*;import java.util.*;public class Main{public static void main(String[]a)throws Exception{Scanner s=new Scanner(new File("input.txt"));PrintWriter o=new PrintWriter("output.txt");o.print(s.nextInt()+s.nextInt());o.close();}}',
    }
    r = DockerJudge().grade(
        sources[language],
        language,
        [TestCase(b"2 3", b"5", 10)],
        limits=Limits(memory_mib=512),
        io_mode="file",
    )
    assert r.verdict == "Accepted", r


def test_wa_partial_ce_tle_runtime_output_and_oom():
    judge = DockerJudge()
    r = judge.grade(
        SOURCES["c"], "c", [TestCase(b"2 3", b"5\n", 5), TestCase(b"3 4", b"8\n", 5)]
    )
    assert r.verdict == "Wrong Answer" and r.score == 5
    assert (
        judge.grade("not valid C", "c", [TestCase(b"", b"")]).verdict == "Compile Error"
    )
    assert (
        judge.grade(
            "int main(){while(1){}}", "c", [TestCase(b"", b"")], Limits(time_ms=100)
        ).verdict
        == "Time Limit Exceeded"
    )
    assert (
        judge.grade("int main(){return 9;}", "c", [TestCase(b"", b"")]).verdict
        == "Runtime Error"
    )
    assert (
        judge.grade(
            "#include <stdio.h>\nint main(){while(1)putchar(65);}",
            "c",
            [TestCase(b"", b"")],
            Limits(output_bytes=1024),
        ).verdict
        == "Runtime Error"
    )
    source = "#include <stdlib.h>\n#include <string.h>\nint main(){while(1){void*p=malloc(1048576);if(p)memset(p,1,1048576);}}"
    assert (
        judge.grade(
            source, "c", [TestCase(b"", b"")], Limits(time_ms=10000, memory_mib=64)
        ).verdict
        == "Memory Limit Exceeded"
    )
