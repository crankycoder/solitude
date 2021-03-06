import json

from nose.tools import eq_

from lib.sellers.models import (Seller, SellerProduct, SellerBluevia,
                                SellerPaypal)
from solitude.base import APITest

uuid = 'sample:uid'


class TestSeller(APITest):

    def setUp(self):
        self.api_name = 'generic'
        self.list_url = self.get_list_url('seller')

    def test_add(self):
        res = self.client.post(self.list_url, data={'uuid': uuid})
        eq_(res.status_code, 201)
        eq_(Seller.objects.filter(uuid=uuid).count(), 1)

    def test_add_multiple(self):
        self.client.post(self.list_url, data={'uuid': uuid})
        res = self.client.post(self.list_url, data={'uuid': uuid})
        eq_(res.status_code, 400)
        eq_(self.get_errors(res.content, 'uuid'),
            ['Seller with this Uuid already exists.'])

    def test_add_empty(self):
        res = self.client.post(self.list_url, data={'uuid': ''})
        eq_(res.status_code, 400)
        eq_(self.get_errors(res.content, 'uuid'), ['This field is required.'])

    def test_add_missing(self):
        res = self.client.post(self.list_url, data={})
        eq_(res.status_code, 400)
        eq_(self.get_errors(res.content, 'uuid'), ['This field is required.'])

    def test_list_allowed(self):
        self.allowed_verbs(self.list_url, ['post', 'get'])

    def create(self):
        return Seller.objects.create(uuid=uuid)

    def test_get(self):
        obj = self.create()
        res = self.client.get(self.get_detail_url('seller', obj))
        eq_(res.status_code, 200)
        content = json.loads(res.content)
        eq_(content['uuid'], uuid)
        eq_(content['resource_pk'], obj.pk)


class TestSellerPaypal(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.seller = Seller.objects.create(uuid=uuid)
        self.list_url = self.get_list_url('seller')

    def data(self):
        return {'seller': '/generic/seller/%s/' % self.seller.pk,
                'paypal_id': 'foo@bar.com',
                'address_one': '123 main st.',
                'country': 'canada'}

    def test_post(self):
        res = self.client.post(self.list_url, data=self.data())
        eq_(res.status_code, 201)
        objs = SellerPaypal.objects.all()
        eq_(objs.count(), 1)
        eq_(objs[0].paypal_id, 'foo@bar.com')
        eq_(objs[0].address_one, '123 main st.')

    def test_get(self):
        obj = self.create()
        url = self.get_detail_url('seller', obj)
        res = self.client.get(url)
        eq_(res.status_code, 200)
        eq_(json.loads(res.content)['token'], False)
        eq_(json.loads(res.content)['secret'], False)

    def test_get_generic(self):
        self.create()
        url = self.get_detail_url('seller', self.seller, api_name='generic')
        res = self.client.get(url)
        eq_(res.status_code, 200)
        content = json.loads(res.content)
        eq_(content['paypal']['token'], False)
        eq_(content['paypal']['secret'], False)

    def create(self):
        return SellerPaypal.objects.create(seller=self.seller,
                                           address_one='123 main st.')

    def test_booleans(self):
        obj = self.create()
        url = self.get_detail_url('seller', obj)

        res = self.client.get(url, data={'uuid': uuid})
        content = json.loads(res.content)
        eq_(content['secret'], False)
        eq_(content['token'], False)

        obj.token = obj.secret = 'abc'
        obj.save()

        res = self.client.get(url, data={'uuid': uuid})
        content = json.loads(res.content)
        eq_(content['secret'], True)
        eq_(content['token'], True)

    def test_set_paypal_id(self):
        obj = self.create()
        url = self.get_detail_url('seller', obj)
        id_ = 'foo@bar.com'
        res = self.client.put(url, data={'paypal_id': id_})
        eq_(res.status_code, 202)
        eq_(json.loads(res.content)['paypal_id'], id_)

    def test_patch(self):
        obj = self.create()
        url = self.get_detail_url('seller', obj)
        id_ = 'foo@bar.com'
        secret = 'some-secret'
        obj.secret = secret
        obj.save()

        res = self.client.patch(url, data={'paypal_id': id_})
        eq_(res.status_code, 202, res.content)
        res = SellerPaypal.objects.get(pk=obj.pk)
        eq_(res.secret, secret)
        eq_(res.paypal_id, id_)
        eq_(res.address_one, '123 main st.')

    def test_list_allowed(self):
        obj = self.create()
        url = self.get_detail_url('seller', obj)

        self.allowed_verbs(self.list_url, ['post', 'get'])
        self.allowed_verbs(url, ['get', 'delete', 'put', 'patch'])


class TestSellerBluevia(APITest):

    def setUp(self):
        self.api_name = 'bluevia'
        self.seller = Seller.objects.create(uuid=uuid)
        self.list_url = self.get_list_url('seller')

    def data(self):
        return {'seller': '/generic/seller/%s/' % self.seller.pk,
                'bluevia_id': 'foo@bar.com'}

    def test_post(self):
        res = self.client.post(self.list_url, data=self.data())
        eq_(res.status_code, 201)
        objs = SellerBluevia.objects.all()
        eq_(objs.count(), 1)
        eq_(objs[0].bluevia_id, 'foo@bar.com')

    def create(self):
        return SellerBluevia.objects.create(seller=self.seller)

    def test_list_allowed(self):
        obj = self.create()
        url = self.get_detail_url('seller', obj)

        self.allowed_verbs(self.list_url, ['post', 'get'])
        self.allowed_verbs(url, ['get', 'delete', 'put', 'patch'])

    def test_patch(self):
        obj = self.create()
        url = self.get_detail_url('seller', obj)
        id_ = 'foo@bar.com'

        res = self.client.patch(url, data={'bluevia_id': id_})
        eq_(res.status_code, 202, res.content)
        res = SellerBluevia.objects.get(pk=obj.pk)
        eq_(res.bluevia_id, id_)


class TestSellerProduct(APITest):

    def setUp(self):
        self.api_name = 'generic'
        self.seller = Seller.objects.create(uuid=uuid)
        self.list_url = self.get_list_url('product')

    def data(self):
        return {'seller': '/generic/seller/%s/' % self.seller.pk,
                'secret': 'hush'}

    def test_post(self):
        res = self.client.post(self.list_url, data=self.data())
        eq_(res.status_code, 201)
        objs = SellerProduct.objects.all()
        eq_(objs.count(), 1)

    def create(self):
        return SellerProduct.objects.create(seller=self.seller)

    def create_url(self):
        obj = self.create()
        url = self.get_detail_url('product', obj)
        return obj, url

    def test_list_allowed(self):
        obj, url = self.create_url()

        self.allowed_verbs(self.list_url, ['post'])
        self.allowed_verbs(url, ['get', 'put', 'patch'])

    def test_patch_get(self):
        obj, url = self.create_url()

        res = self.client.patch(url, json.dumps({'secret': 'hush'}))
        eq_(res.status_code, 202)
        res = self.client.get(url)
        eq_(json.loads(res.content)['secret'], 'hush')

    def test_put_get(self):
        obj, url = self.create_url()

        res = self.client.put(url, json.dumps({'secret': 'hush'}))
        eq_(res.status_code, 202)
        eq_(obj.reget().secret, 'hush')
