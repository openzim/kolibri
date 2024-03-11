import concurrent.futures as cf
from time import sleep
import functools

from datetime import datetime

# Without callbacks
#
# Expected behavior
# t0: all nodes added to the working queue, node 0 and node 1 starts
# t3: node 0 submits video 0
#     node 0 and node 1 complete
#     video 0 starts
#     node 2 and node 3 starts
# t6: node 2 submits video 2
#     node 2 and node 3 completes
#     node 4 and node 5 starts
# t6.5: video 0 fails
#       video 2 starts
# t7: checks detects that exception occured and cancels everything
# finished
#
# Real behavior with ThreadPoolExecutor (not perfect - ru
# nning tasks are continuing till
# they end, but more or less ok)
# t0: all nodes added to the working queue, node 0 and node 1 starts
# t3: node 0 submits video 0
#     node 0 and node 1 complete
#     video 0 starts
#     node 2 and node 3 starts
# t6: node 2 submits video 2
#     node 2 and node 3 completes
#     node 4 and node 5 starts
# t6.5: video 0 fails
#       video 2 starts
# t7: checks detects that exception occured and cancels everything
# t8: node 4 and node 5 completes <== UNEXPECTED
# t10: video 2 completes <== UNEXPECTED
# finished

# ---------------
# With callbacks
# ---------------
#
# With callbacks, the callback is executed at the end of the future, in "main" thread,
# so we assume it will delay the start of the next future
#
# Expected behavior with callbacks
# t0: all nodes added to the working queue
#     node 0 and node 1 starts
# t3: node 0 submits video 0
#     node 0 and node 1 complete
#     video 0 starts
#     callbacks of node 0 and node 1 starts
# t4: callbacks of node 0 and node 1 completes
#     node 2 and node 3 starts
# t6.5: video 0 fails
#       callback of video 0 starts
# t7: node 2 and node 3 completes
#     callbacks of node 2 and node 3 starts
#     checks detects that exception occured and cancels everything
# t7.5: callback of video 0 completes
# t8: callbacks of node 2 and node 3 completes
# finished
#
#
# Real behavior with ThreadPoolExecutor (a real mess, way too many things are executed)
# t0: all nodes added to the working queue
#     node 0 and node 1 starts
# t3: node 0 submits video 0
#     node 0 and node 1 complete
#     video 0 starts
#     callbacks of node 0 and node 1 starts
# t4: callbacks of node 0 and node 1 completes
#     node 2 and node 3 starts
# t6.5: video 0 fails
#       callback of video 0 starts
# t7: node 2 and node 3 completes
#     callbacks of node 2 and node 3 starts
#     checks detects that exception occured and cancels everything
#     callback of node 4 starts <= WHY?, future did not even started
# t7.5: callback of video 0 completes
#     video 2 starts <= WHY? we are supposed to cancel futures, not start new ones
# t8: callbacks of node 2 and node 3 completes
#     node 5 and node 6 starts <= WHY?
# t11: video 2 complete <= WHY?
#     callback of video 2 starts <= WHY?
#     node 5 and node 6 complete
#     callback of node 5 and node 6 starts <= WHY?
# t12: callback of video 2 complete
#     video 6 starts <= WHY?
#     callback of node 5 and node 6 completes
# t15: video 6 completes
#     callback of video 6 starts <= WHY?
# t16: call of video 6 complete
# finished

# Alter this to activate/deactivate callbacks
WITH_CALLBACKS = True

start = datetime.now()


def log(message: str):
    print(f"{round((datetime.now() - start).total_seconds(), 1)} - {message}")


def wait_for(seconds: float):
    mystart = datetime.now()
    while (datetime.now() - mystart).total_seconds() < seconds:
        pass


def node_callback(future: cf.Future, a: int):
    log(f"Node {a} callback started")
    wait_for(1)
    log(f"Node {a} callback finished")


def video_callback(future: cf.Future, a: int):
    log(f"Video {a} callback started")
    wait_for(1)
    log(f"Video {a} callback finished")


def process_video(a: int):
    log(f"Video {a} started")
    wait_for(3.5)
    if a < 1:
        log(f"Video {a} failed")
        raise Exception(f"Video problem with {a}")
    log(f"Video {a} completed")


def process_node(a: int):
    log(f"Node {a} started")
    wait_for(3)
    if a % 2 == 0:
        future = videos_executor.submit(process_video, a)
        videos_futures.add(future)
        if WITH_CALLBACKS:
            future.add_done_callback(functools.partial(video_callback, a=a))
    log(f"Node {a} completed")


# ProcessPoolExecutor has a very weird behavior, I struggled to make it work as expected
# ThreadPoolExecutor seems to be more stable, even if I don't really know why
nodes_executor = cf.ThreadPoolExecutor(max_workers=2)
videos_executor = cf.ThreadPoolExecutor(max_workers=1)

nodes_futures: set[cf.Future] = set()
videos_futures: set[cf.Future] = set()

for a in range(7):
    future = nodes_executor.submit(process_node, a)
    nodes_futures.add(future)
    if WITH_CALLBACKS:
        future.add_done_callback(functools.partial(node_callback, a=a))

while True:
    # we cannot use the cf.wait since videos_futures is not yet set (it needs nodes to
    # be started) and we would hence not capture exceptions occuring in nodes_futures
    # cf.wait(nodes_futures | videos_futures, return_when=cf.FIRST_EXCEPTION)
    wait_for(1)
    # log("Checking status")
    if (
        sum(1 if future._exception else 0 for future in nodes_futures | videos_futures)
        > 0
    ):  # we have to use ._exception, because .exception() if waiting for future to
        # complete
        log("Exception encountered")
        break

    if sum(0 if future.done() else 1 for future in nodes_futures | videos_futures) == 0:
        log("All tasks completed")
        break


log(
    f"{sum(1 if future.done() else 0 for future in nodes_futures | videos_futures)} tasks done"
)
log(
    f"{sum(0 if future.done() else 1 for future in nodes_futures | videos_futures)} tasks not done"
)

# this works more or else, because it cancels only futures which were not already
# started + it waits for only running futures to complete before returning, meaning that
# videos futures are cancelled only once the nodes futures have all completed
log("Shutting down nodes")
nodes_executor.shutdown(cancel_futures=True)
log("Shutting down videos")
videos_executor.shutdown(cancel_futures=True)
log("All exectutors shut down")

log(
    f"{sum(1 if future.done() else 0 for future in nodes_futures | videos_futures)} tasks done"
)
log(
    f"{sum(0 if future.done() else 1 for future in nodes_futures | videos_futures)} tasks not done"
)
