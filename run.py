from BIDSHandler.BIDSFolder import BIDSFolder


root1 = "C:\\Users\\MQ20184158\\Documents\\MEG data\\rs_test_data_for_matt\\BIDS\\test1"  # noqa
root2 = "C:\\Users\\MQ20184158\\Documents\\MEG data\\rs_test_data_for_matt\\BIDS\\test2"  # noqa

a = BIDSFolder(root1)
b = BIDSFolder(root2)
subb = b.project('WS001').subject(2)
proja = a.project('WS001')

print(subb)
print(proja)

a.add(subb)
print(proja)
