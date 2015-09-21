CFLAGS=-Wall -Wextra -g3

clean:
	rm *.o

all: lab2

lab2: client-multi.o client-simple.o server-iterative.o
		g++ client-multi.o client-simple.o server-iterative.o -o lab2

client-multi.o: client-multi.cpp
		g++ client-multi.cpp -o client-multi.o -lrt

client-simple.o: client-simple.cpp
		g++ client-simple.cpp -o client-simple.o

server-iterative.o: server-iterative.cpp
		g++ server-iterative.cpp -o server-iterative
