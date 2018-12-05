from BIDSFolder import BIDSFolder


root1 = "C:\\Users\\MQ20184158\\Documents\\MEG data\\rs_test_data_for_matt\\BIDS\\test1"  # noqa
root2 = "C:\\Users\\MQ20184158\\Documents\\MEG data\\rs_test_data_for_matt\\BIDS\\test2"  # noqa

a = BIDSFolder(root1)
b = BIDSFolder(root2)
sa = a.project('WS001').subject(1).session(1)
sb = b.project('WS001').subject(1).session(1)
scan = sb.scan(task='blah', run='1')
print(sa)
print(sb)
print(scan.raw_file)
print(scan.path)
print(scan.info['TaskName'])
print(scan.sidecar)

sa.add(scan)
print(sa)
for scan in sa.scans:
    print(scan.info['TaskName'])
