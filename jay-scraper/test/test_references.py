import unittest


class References(list):

    def append(self, p_object):
        if p_object and not self.contains(p_object):
            super(References, self).append(p_object)

    def contains(self, p_object, keys=("item_id", "item_type")):
        for p in self:
            return_value = True
            for key in keys:
                return_value &= p[key] == p_object[key]
                if not return_value:
                    break
            if return_value:
                return return_value
        return False


class TestReferences(unittest.TestCase):

    def test_contains_0(self):
        lst = References()
        lst.append({"item_id": 1, "item_type": "a"})
        self.assertTrue(lst.contains({"item_id": 1, "item_type": "a", "item_dd": False}))

    def test_contains_1(self):
        lst = References()
        lst.append({"item_id": 1, "item_type": "a", "item_dd": False})
        self.assertTrue(lst.contains({"item_id": 1, "item_type": "a", "item_dd": False}, keys={"item_dd"}))