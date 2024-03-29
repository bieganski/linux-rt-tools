import gdb

#
# gdb --ex 'source THIS_SCRIPT.py' --args 
# /usr/lib/linux-tools/6.2.0-36-generic/bpftool -d prog load .output/minimal.bpf.o /sys/fs/bpf/wtf  
#



# class WriteCatch(gdb.Breakpoint):
#     def stop(self):
#         # Get the string pointed to by RSI
#         string_address = int(gdb.parse_and_eval("$rsi"))
#         string = gdb.execute(f"x/s {string_address}", to_string=True)
#         string = string.split(":")[1].strip()

#         print(f"AAA {string}")

#         # Check if the string starts with "9:"
#         if "9:" in string:
#             return True
#         else:
#             return False


def handler(event):
    string_address = int(gdb.parse_and_eval("$rsi"))
    string = gdb.execute(f"x/s {string_address}", to_string=True)
    # string = string.split(":")[1].strip()

    num_bytes = int(gdb.parse_and_eval("$rdx"))
    if num_bytes > 1000:
        # data = gdb.execute(f"x/{num_bytes}xb {string_address}", to_string=True)
        gdb.execute(f"dump memory output.bin {string_address} {string_address}+{num_bytes}")
        print(f"AAA [{num_bytes}] output.bin")
        gdb.execute(f"bt")
        input()
    # print(event)
    # a= input()

def main():
    gdb.execute("catch syscall write")
    gdb.execute("run")

    gdb.events.stop.connect(handler)

    while True:
        gdb.execute("continue")
        # if WriteCatch().stop():
        #     break

if __name__ == "__main__":
    main()