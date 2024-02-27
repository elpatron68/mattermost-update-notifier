import sched, time

def do_something(scheduler): 
    # schedule the next call first
    print(time.ctime())
    scheduler.enter(60, 1, do_something, (scheduler,))
    print("Doing stuff...")
    # then do your stuff

if __name__ == "__main__":
    my_scheduler = sched.scheduler(time.time, time.sleep)
    my_scheduler.enter(60, 1, do_something, (my_scheduler,))
    my_scheduler.run()