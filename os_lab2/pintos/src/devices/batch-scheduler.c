/* Tests cetegorical mutual exclusion with different numbers of threads.
 * Automatic checks only catch severe problems like crashes.
 */
#include <stdio.h>
#include "tests/threads/tests.h"
#include "threads/malloc.h"
#include "threads/synch.h"
#include "threads/thread.h"
#include "lib/random.h" //generate random numbers
#include "timer.h"

#define BUS_CAPACITY 3
#define SENDER 0
#define RECEIVER 1
#define NORMAL 0
#define HIGH 1

/*
 *	initialize task with direction and priority
 *	call o
 * */
typedef struct {
	int direction;
	int priority;
} task_t;

void batchScheduler(unsigned int num_tasks_send, unsigned int num_task_receive,
        unsigned int num_priority_send, unsigned int num_priority_receive);

void senderTask(void *);
void receiverTask(void *);
void senderPriorityTask(void *);
void receiverPriorityTask(void *);
void init_bus(void);


void oneTask(task_t task);/*Task requires to use the bus and executes methods below*/
	void getSlot(task_t task); /* task tries to use slot on the bus */
	void transferData(void); /* task processes data on the bus either sending or receiving based on the direction*/
	void leaveSlot(task_t task); /* task release the slot */

int tasks = 0;
int currDirection = 0;
int queueSend = 0;
int queueRecv = 0;
int inQueue[2];
int queuePrio = 0;

struct lock lock;
struct condition waitingToSend;
struct condition waitingToRecv;
struct condition* waiting[2];
struct condition waitingPrio;

/* initializes semaphores */
void init_bus(void){

  random_init((unsigned int)123456789);

	lock_init(&lock);
	cond_init(&waitingToSend);
	cond_init(&waitingToRecv);
	cond_init(&waitingPrio);
	waiting[SENDER] = &waitingToSend;
	waiting[RECEIVER] = &waitingToRecv;
	inQueue[SENDER] = queueSend;
	inQueue[RECEIVER] = queueRecv;

}

/*
 *  Creates a memory bus sub-system  with num_tasks_send + num_priority_send
 *  sending data to the accelerator and num_task_receive + num_priority_receive tasks
 *  reading data/results from the accelerator.
 *
 *  Every task is represented by its own thread.
 *  Task requires and gets slot on bus system (1)
 *  process data and the bus (2)
 *  Leave the bus (3).
 */

void batchScheduler(unsigned int num_tasks_send, unsigned int num_tasks_receive,
        unsigned int num_priority_send, unsigned int num_priority_receive)
{
	unsigned int i;
	tid_t thread;

	for (i = 0; i < num_tasks_send; i++) {
		thread = thread_create("thread", NORMAL, &senderTask, NULL);
	}

	for (i = 0; i < num_tasks_receive; i++) {
		thread = thread_create("thread", NORMAL, &receiverTask, NULL);
	}

	for (i = 0; i < num_priority_send; i++) {
		thread = thread_create("thread", HIGH, &senderPriorityTask, NULL);
	}

	for (i = 0; i < num_priority_receive; i++) {
		thread = thread_create("thread", HIGH, &senderPriorityTask, NULL);
	}
}

/* Normal task,  sending data to the accelerator */
void senderTask(void *aux UNUSED){
  task_t task = {SENDER, NORMAL};
  oneTask(task);
}

/* High priority task, sending data to the accelerator */
void senderPriorityTask(void *aux UNUSED){
  task_t task = {SENDER, HIGH};
  oneTask(task);
}

/* Normal task, reading data from the accelerator */
void receiverTask(void *aux UNUSED){
  task_t task = {RECEIVER, NORMAL};
  oneTask(task);
}

/* High priority task, reading data from the accelerator */
void receiverPriorityTask(void *aux UNUSED){
  task_t task = {RECEIVER, HIGH};
  oneTask(task);
}

/* abstract task execution*/
void oneTask(task_t task) {
  getSlot(task);
  transferData();
  leaveSlot(task);
}

/* task tries to get slot on the bus subsystem */
void getSlot(task_t task) {

	// https://pingpong.chalmers.se/courseId/5850/node.do?id=2715451&ts=1448981096052&u=-2096496696

	lock_acquire(&lock);
	printf("Getting slot...");


	// while no space on bus - wait...
	while ((tasks == 3) || (tasks > 0 && currDirection != task.direction)) {
		if (task.priority == HIGH) {
			queuePrio++;
			cond_wait(&waitingPrio, &lock);
			queuePrio--;
		}

		else {
			inQueue[task.direction]++;
			cond_wait(waiting[task.direction], &lock);
			inQueue[task.direction]--;
		}
	}

	// get on the bus
	tasks++;
	currDirection = task.direction;

	if (task.priority == HIGH)
		printf("Prio task got slot!");

	lock_release(&lock);
}

/* task processes data on the bus send/receive */
void transferData() {
  //printf("Transferring data...");
	timer_usleep(random_ulong() % 100);
	//printf("Transfer complete!");
}

/* task releases the slot */
void leaveSlot(task_t task) {
	lock_acquire(&lock);

	// done on the bus
	tasks--;

	// If anyone in prio queue, signal them
	if (queuePrio > 0) {
		cond_broadcast(&waitingPrio, &lock);
	}

	// If anyone waiting to go same direction, wake them
	// Why not broadcast?
	else {
		if (inQueue[currDirection] > 0) {
			cond_signal(waiting[currDirection], &lock);
		}
		// Else wake up everyone going other way
		else if (tasks == 0) {
			cond_broadcast(waiting[1-currDirection], &lock);
		}
	}

	lock_release(&lock);

	printf("Left slot!");
}
