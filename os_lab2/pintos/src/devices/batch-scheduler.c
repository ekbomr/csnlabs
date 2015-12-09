/* Tests cetegorical mutual exclusion with different numbers of threads.
 * Automatic checks only catch severe problems like crashes.
 */
#include <stdio.h>
#include "tests/threads/tests.h"
#include "threads/malloc.h"
#include "threads/synch.h"
#include "threads/thread.h"
#include "lib/random.h" //generate random numbers

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


void oneTask(task_t task);/*Task requires to use the bus and executes methods below*/
	void getSlot(task_t task); /* task tries to use slot on the bus */
	void transferData(task_t task); /* task processes data on the bus either sending or receiving based on the direction*/
	void leaveSlot(task_t task); /* task release the slot */

/* Threads inherit mem from parent?? */
int waitingToSend = 0;
int waitingToRecv = 0;
int activeSend = 0;
int activeRecv = 0;
struct semaphore lock;
struct semaphore sendWait;
struct semaphore recvWait;
struct semaphore[2] active;

/* initializes semaphores */
void init_bus(void){

  random_init((unsigned int)123456789);

	sema_init (&lock, 1);
	sema_init (&readWait, 3);
	sema_init (&writeWait, 3);
	active[0] = sendWait;
	active[1] = recvWait;

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

void batchScheduler(unsigned int num_tasks_send, unsigned int num_task_receive,
        unsigned int num_priority_send, unsigned int num_priority_receive)
{

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
  transferData(task);
  leaveSlot(task);
}


/* task tries to get slot on the bus subsystem */
void getSlot(task_t task)
{
	// int waitingToSend = 0;
	// int waitingToRecv = 0;
	// int activeSend = 0;
	// int activeRecv = 0;

	/* "Inspiration" */
	/* http://www.cs.umd.edu/~hollings/cs412/s96/synch/eastwest.html */

	while (1) {
		sema_down(lock);

		if (task->direction == SENDER && activeSend < 3 && activeRecv == 0) {
			activeSend++;
			sema_up(lock);
			sema_down(active[SENDER]);
			return;
		}
		else {
			/* Block until sender slot available */
			sema_up(lock);
			sema_down(active[SENDER]);
		}

		if (task->direction == RECEIVER && activeRecv < 3 && activeSend == 0) {
			activeRecv++;
			sema_up(lock);
			sema_down(active[RECEIVER]);
			return;
		}
		else {
			/* Block until receiver slot available */
			sema_up(lock);
			sema_down(active[RECEIVER]);
		}

	}

}

/* task processes data on the bus send/receive */
void transferData(task_t task)
{
  msg("Transferring data...");
	timer_usleep(random_ulong() % 100);
}

/* task releases the slot */
void leaveSlot(task_t task)
{
	sema_down(lock);
	if (task->direction == SENDER) {
		activeSend--;
		sema_up(active[SENDER])
	}
	else {
		activeRecv--;
		sema_up(active[RECEIVER])
	}
	sema_up(lock);
}
