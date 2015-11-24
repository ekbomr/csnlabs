/*
 * Main source code file for lsh shell program
 *
 * You are free to add functions to this file.
 * If you want to add functions in a separate file
 * you will need to modify Makefile to compile
 * your additional functions.
 *
 * Add appropriate comments in your code to make it
 * easier for us while grading your assignment.
 *
 * Submit the entire lab1 folder as a tar archive (.tgz).
 * Command to create submission archive:
      $> tar cvf lab1.tgz lab1/
 *
 * All the best
 */

 #include <stdio.h>
 #include <stdlib.h>
 #include <readline/readline.h>
 #include <readline/history.h>
 #include "parse.h"
 #include <unistd.h>
 #include <sys/wait.h>
 #include <string.h>
 #include <signal.h>
 #include <sys/types.h>
 #include <errno.h>
 #include <fcntl.h>

/* When non-zero, this global means the user is done using this program. */
int done = 0;

pid_t pid;
int status;
sig_atomic_t child_exit_status;
struct sigaction sigchld_action, sigint_action;

/*
 * Function declarations
 */

void PrintCommand(int, Command *);
void PrintPgm(Pgm *);
void stripwhite(char *);
void clean_up_child_process(int signal_number);
void handle_sigint(int signal_number);
void execNextPgm (Pgm *nextPgm);

int main(void){

  Command cmd;
  int n;
  /* Handle the termination of a child process */
  memset(&sigint_action, 0, sizeof (sigint_action));
  sigint_action.sa_handler = &handle_sigint;
  sigaction(SIGINT, &sigint_action, NULL);

  while (!done) {
    char buf[1024];
    char *line;
    getcwd(buf, sizeof(buf));
    strcat(buf, " > ");

    line = readline(buf);

    if (!line) {
      /* Encountered EOF at top level */
      done = 1;
    }
    else {
      char *usrcmd;
      /*
       * Remove leading and trailing whitespace from the line
       * Then, if there is anything left, add it to the history list
       * and execute it.
       */
      stripwhite(line);
      if(*line) {
        add_history(line);
        /* execute it */
        n = parse(line, &cmd);
        PrintCommand(n, &cmd);

        usrcmd = cmd.pgm->pgmlist[0];
        if (strcmp(usrcmd, "exit") == 0) {
          return 0;
        }
        else if (strcmp(usrcmd, "cd") == 0) {
          /* If path arg given to cd, navigate there */
          if (cmd.pgm->pgmlist[1]) {
            chdir(cmd.pgm->pgmlist[1]);
          }
          /* Else, cd to home dir */
          else {
            chdir(getenv("HOME"));
          }
          continue;
        }

        else {
          Pgm *nextPgm;
          nextPgm = cmd.pgm;

          pid = fork();
          if (pid < 0) {
            printf("Fork error: %s\n", strerror(errno));
          }

          /* Child process code */
          else if (pid == 0) {
            /* Redirect input/output if *file* > *cmd* */
            if (cmd.rstdin != NULL) {
              int read_fd;
              read_fd = open(cmd.rstdin, O_RDONLY);
              dup2(read_fd, STDIN_FILENO);
            }

            if (cmd.rstdout != NULL) {
              int write_fd;
              write_fd = open(cmd.rstdout, O_TRUNC | O_CREAT | O_WRONLY);
              dup2(write_fd, STDOUT_FILENO);
            }

            if (cmd.background) {
              //close(STDIN_FILENO);
              /* Change process group to prevent SIGINT kill bg process */
              setpgid(pid, 0);
            }
            execNextPgm(nextPgm);
          }

          /* Parent process code */
          else {
            memset(&sigchld_action, 0, sizeof (sigchld_action));
            sigchld_action.sa_handler = &clean_up_child_process;
            sigaction(SIGCHLD, &sigchld_action, NULL);

            if (!cmd.background) {
              if (waitpid(pid, &status, 0) != pid) {
                printf("Wait error: %s\n", strerror(errno));
              }
            }
          }
        }
      }
    }

    if(line) {
      free(line);
    }
  }
  return 0;
}


/* execNextPgm: Recursively executes multiple programs */
void execNextPgm (Pgm *nextPgm) {
  /* Base case */
  if (nextPgm->next == NULL) {
    if(execvp(nextPgm->pgmlist[0], nextPgm->pgmlist) < 0){
      perror("Exec error");
      exit(EXIT_FAILURE);
    }
  }

  else {
    /* Declare and init pipe */
    int pipe_fds[2];
    int read_fd;
    int write_fd;
    pipe(pipe_fds);
    read_fd = pipe_fds[0];
    write_fd = pipe_fds[1];

    pid = fork();
    if (pid < 0) {
      printf("Fork error: %s\n", strerror(errno));
    }

    /* (Grand)child process code */
    else if (pid == 0) {
      /* Redirect output to pipe before executing */
      dup2(write_fd, STDOUT_FILENO);
      close(write_fd);
      close(read_fd);
      /* Point to next program and execute recursively */
      nextPgm = nextPgm->next;
      execNextPgm(nextPgm);
    }

    /* Parent process code */
    else {
      /* Redirect input to pipe before waiting for child */
      dup2(read_fd, STDIN_FILENO);
      close(read_fd);
      close(write_fd);
      if (waitpid(pid, &status, 0) != pid) {
        printf("Wait status message: %i\n", status);
      }
      /* Execute after waiting to get input from child */
      if(execvp(nextPgm->pgmlist[0], nextPgm->pgmlist) < 0){
        printf("Exec error: %s\n", strerror(errno));
        exit(EXIT_FAILURE);
      }
    }
  }
}

/* Clean up the child process. */
void clean_up_child_process (int signal_number){
  int status;
  wait(&status);
  /* Store its exit status in a global variable. */
  child_exit_status = status;
}

/* Intercept SIGINT for the parent to keep the shell from terminating */
void handle_sigint (int signal_number){
  /* Do nothing */
}

/*
 * Name: PrintCommand
 *
 * Description: Prints a Command structure as returned by parse on stdout.
 *
 */
void PrintCommand (int n, Command *cmd){
  printf("Parse returned %d:\n", n);
  printf("   stdin : %s\n", cmd->rstdin  ? cmd->rstdin  : "<none>" );
  printf("   stdout: %s\n", cmd->rstdout ? cmd->rstdout : "<none>" );
  printf("   bg    : %s\n", cmd->background ? "yes" : "no");
  PrintPgm(cmd->pgm);
}

/*
 * Name: PrintPgm
 *
 * Description: Prints a list of Pgm:s
 *
 */
void PrintPgm (Pgm *p){
  if (p == NULL) {
    return;
  }
  else {
    char **pl = p->pgmlist;

    /* The list is in reversed order so print
     * it reversed to get right
     */
    PrintPgm(p->next);
    printf("    [");
    while (*pl) {
      printf("%s ", *pl++);
    }
    printf("]\n");
  }
}

/*
 * Name: stripwhite
 *
 * Description: Strip whitespace from the start and end of STRING.
 */
void stripwhite (char *string){
  register int i = 0;

  while (whitespace( string[i] )) {
    i++;
  }

  if (i) {
    strcpy (string, string + i);
  }

  i = strlen( string ) - 1;
  while (i> 0 && whitespace (string[i])) {
    i--;
  }

  string[++i] = '\0';
}
