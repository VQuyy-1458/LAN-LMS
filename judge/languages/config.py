LANGUAGES={
 'c':('Main.c',['gcc','-std=c17','-O2','/source/Main.c','-o','/artifacts/program'],['/artifacts/program']),
 'cpp':('Main.cpp',['g++','-std=c++17','-O2','/source/Main.cpp','-o','/artifacts/program'],['/artifacts/program']),
 'java':('Main.java',['javac','-d','/artifacts','/source/Main.java'],['java','-Xmx128m','-XX:CompressedClassSpaceSize=32m','-XX:ReservedCodeCacheSize=32m','-Xss256k','-XX:+UseSerialGC','-cp','/artifacts','Main'])
}
