month_dict = {
    1: "Jan",
    2: "feb",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "Aug",
    9: "Sept",
    10: "Oct",
    11: "November",
    12: "December",
}

num = int(input("Enter the month num: "))
if num in month_dict:
    print(f"The month is {month_dict[num]}")

else:
    print("wrong query")
