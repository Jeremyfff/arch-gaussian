import datetime


def print_current_time():
    print(datetime.datetime.now().strftime('(%)'))


if __name__ == '__main__':
    print_current_time()
