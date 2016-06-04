from unittest import TestCase

import types
import os

from dstruct import (HasDescriptors, BaseDescriptor, DataStruct, DataField,
	FieldError, dataparser, datafield, DataStructFromJSON, DataStructFromCSV)

class TestHasDescriptors(TestCase):

	def test_member_setup(self):

		class A(HasDescriptors):
			x = BaseDescriptor()
		class B(A):
			y = BaseDescriptor()

		self.assertIs(B.x.this_class, A)
		self.assertEqual(B.x.this_name, 'x')
		self.assertIs(B.y.this_class, B)
		self.assertEqual(B.y.this_name, 'y')

	def test_instance_setup(self):

		class Member(BaseDescriptor):
			testcase = self
			def init_inst(self, inst):
				self.testcase.assertTrue(hasattr(inst, 'members'))
				inst.members.append(self)

		class A(HasDescriptors):
			x = Member()
			def setup_self(self):
				self.members = []
				super(A, self).setup_self()
		class B(A):
			y = Member()

		b = B()
		self.assertEqual(len(b.members), 2)
		self.assertEqual(set(b.members),set([B.x, B.y]))


class TestDataStruct(TestCase):

	def test_fields(self):
		class A(DataStruct):
			x = DataField()
		class B(A):
			y = DataField()
		class C(B):
			y = DataField()

		self.assertEqual(C.fields(), {'x': A.x, 'y': C.y})

	def test_class_owned_fields(self):
		class A(DataStruct):
			x = DataField()
		class B(A):
			y = DataField()

		self.assertEqual(B.class_owned_fields(), {'y': B.y})

	def test_add_and_del_field(self):

		class A(DataStruct):
			x = DataField()
		class B(A): pass

		b = B()

		initial = (b.fields(), b.class_owned_fields())

		yf, zf = DataField(), DataField()
		b.add_fields(y=yf, z=zf)

		# check fields initialized
		self.assertEqual(yf.this_name, 'y')
		self.assertIs(yf.this_class, b.__class__)
		self.assertEqual(zf.this_name, 'z')
		self.assertIs(zf.this_class, b.__class__)

		# check that instance knows about new fields
		self.assertEqual(b.fields(), {'x': A.x, 'y': yf, 'z': zf})
		self.assertEqual(b.class_owned_fields(), {'y': yf, 'z': zf})

		class_fields = B.fields()
		b.del_fields('y', 'z')
		# check that we've deleted all the new fields
		final = (b.fields(), b.class_owned_fields())
		self.assertEqual(initial, final)
		# check that the original class wasn't touched
		self.assertEqual(class_fields, B.fields())


class TestDataField(TestCase):

	def test_get_set_field(self):
		class A(DataStruct):
			x = DataField()
		a = A()
		a.x = 0
		self.assertEqual(a.x, 0)

	def test_inline_field_parser(self):
		class A(DataStruct):
			x = DataField(parser=lambda v: v+1)
		a = A()
		a.x = 0
		self.assertEqual(a.x, 1)

	def test_data_field_decorator(self):
		class A(DataStruct):
			def __init__(self):
				self.v = 1
			@datafield
			def x(self, data):
				return self.v + data
		a = A()
		a.x = 0
		self.assertEqual(a.x, 1)

	def test_field_from_data(self):
		class A(DataStruct):
			x = DataField('m', 'n')
		a = A({'m': {'n': 0}})
		self.assertEqual(a.x, 0)


class TestDataParser(TestCase):

	def test_basic_usage(self):
		with self.assertRaises(ValueError):
			# func must be callable
			dataparser(func='a')

		with self.assertRaises(ValueError):
			# only raises if func passed
			# method_type keywork is a bool
			dataparser(method_type=None)

		with self.assertRaises(ValueError):
			# expects function type
			# with decorator notation
			class A(object):
				def __call__(self): pass
			dataparser()(A())

	def test_struct_install(self):
		with self.assertRaises(AttributeError):
			# no attribute 'y' in struct
			class A(DataStruct):
				x = DataField()
				@dataparser('x', 'y')
				def parser(self, data):
					pass

		with self.assertRaises(FieldError):
			# no field 'y' in struct
			class A(DataStruct):
				x = DataField()
				y = 1
				@dataparser('x', 'y')
				def parser(self, data):
					pass

		def f(self, data):
			pass

		class A(DataStruct):
			x = DataField()
			y = DataField()
			# use the kwargs notation
			parser1 = dataparser('x', 'y', method_type=True, func=f)
			# simulate decorator notation
			parser2 = dataparser('x', 'y')(f)

		for p in (A.parser1, A.parser2):
			self.assertTrue(p.method_type)
			self.assertEqual(p.names, ('x', 'y'))
			self.assertEqual(p._func, f)

		a = A()
		for p in (a.parser1, a.parser2):
			self.assertTrue(isinstance(p, types.MethodType))

	def test_field_parsing(self):
		class A(DataStruct):
			def __init__(self):
				self.v = 1
			x = DataField()
			@dataparser('x')
			def x_parser(self, data):
				return self.v + data
		a = A()
		a.x = 0
		self.assertEqual(a.x, 1)

from tempfile import mkstemp

def pytemp(filetype, content=None):
	fd, fname = mkstemp(filetype)
	f = os.fdopen(fd, 'w')
	if content is not None:
		f.write(content)
	f.close()
	return fname

from ._filetext import *

class TestLoadedStruct(TestCase):

	def test_loaded_json_struct(self):

		class AccountSummaryFromJSON(DataStructFromJSON):
		    user = DataField()
		    type = DataField('account', 'account-type')
		    ballance = DataField('account', 'account-ballance')
		    # you can pass functions under the keyword "parser" to parse raw data parsing
		    account_number = DataField('account', 'account-number', parser=lambda s: 'X'*len(s[:-4])+s[-4:])

		filename = pytemp('.json', bank_data_json)
		asum = AccountSummaryFromJSON(filename)

		expected = {"ballance": 1234.56,
					"type": "checking",
					"user": "John F. Doe",
					"account_number": "XXXXX6789"}
		self.assertEqual(asum, expected)

	def test_loaded_csv_struct(self):
		class AverageUserFromCSV(DataStructFromCSV):
		    @datafield(path=None)
		    def age(self, data):
		        total = 0
		        for name in data:
		            total += int(data[name]['Age'])
		        return round(float(total)/len(data), 1)
		    @datafield(path=None)
		    def weight(self, data):
		        total = 0
		        for name in data:
		            total += int(data[name]['Weight'])
		        return round(float(total)/len(data), 1)

		# narrow vs wide can sometimes be infered
		filename = pytemp('.csv', narrow_csv)
		narrow = AverageUserFromCSV(filename)
		filename = pytemp('.csv', wide_csv)
		wide = AverageUserFromCSV(filename)

		expected = {"age": 40.0, "weight": 174.3}
		self.assertEqual(narrow, expected)
		self.assertEqual(narrow, wide)
