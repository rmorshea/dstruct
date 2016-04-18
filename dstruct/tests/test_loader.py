
def test_csv_loader():
	w = CSVLoader('utils/wide.csv').load()
	n = CSVLoader('utils/narrow.csv', wideform=False)
	assert w.load() == n.load()