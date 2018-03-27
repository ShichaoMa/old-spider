# -*- coding:utf-8 -*-
import copy
import json


def split_item(item, flags, batch_size=1024*1024):
    if len(json.dumps(item)) < batch_size:
        return [item]
    skus = item["items"][0]["items"]

    base_info = copy.deepcopy(item)
    base_info["items"][0]["albums"] = dict()
    base_info["items"][0]["bullets"]["description"] = dict()
    base_info["items"][0]["bullets"]["title"] = dict()
    base_info["items"][0]["bullets"]["feature"] = dict()
    base_info["items"][0]["bullets"]["spec"] = dict()
    base_info["items"][0]["meta"]["all_skus"] = False
    albums = item["items"][0]["albums"]
    descriptions = item["items"][0]["bullets"]["description"]
    titles = item["items"][0]["bullets"]["title"]
    features = item["items"][0]["bullets"]["feature"]
    specs = item["items"][0]["bullets"]["spec"]

    items = list()
    new_item = copy.deepcopy(base_info)

    for sku in sorted(skus, key=lambda sku: tuple(sku[flag] for flag in flags)):
        have_change = dict()
        if sku["album"] not in new_item["items"][0]["albums"]:
            new_item["items"][0]["albums"][sku["album"]] = albums[sku["album"]]
            have_change["albums"] = sku["album"]
        if sku["bullets"]["description_id"] and sku["bullets"]["description_id"] not in new_item["items"][0]["bullets"]["description"]:
            new_item["items"][0]["bullets"]["description"][sku["bullets"]["description_id"]] = descriptions[sku["bullets"]["description_id"]]
            have_change["descriptions"] = sku["bullets"]["description"]
        if sku["bullets"]["feature_id"] and sku["bullets"]["feature_id"] not in new_item["items"][0]["bullets"]["feature"]:
            new_item["items"][0]["bullets"]["feature"][sku["bullets"]["feature_id"]] = features[sku["bullets"]["feature_id"]]
            have_change["features"] = sku["bullets"]["feature"]
        if sku["bullets"]["spec_id"] and sku["bullets"]["spec_id"] not in new_item["items"][0]["bullets"]["spec"]:
            new_item["items"][0]["bullets"]["spec"][sku["bullets"]["spec_id"]] = specs[sku["bullets"]["spec_id"]]
            have_change["specs"] = sku["bullets"]["spec"]
        if sku["bullets"]["title_id"] and sku["bullets"]["title_id"] not in new_item["items"][0]["bullets"]["title"]:
            new_item["items"][0]["bullets"]["title"][sku["bullets"]["title_id"]] = titles[sku["bullets"]["title_id"]]
            have_change["titles"] = sku["bullets"]["title"]
        if have_change and len(json.dumps(new_item)) > batch_size:
            for name, value in have_change.items():
                if name == "albums":
                    del new_item["items"][0][name][value]
                else:
                    del new_item["items"][0]["bullets"][name][value]
            items.append(new_item)
            new_item = copy.deepcopy(base_info)
            new_item["items"][0]["albums"][sku["album"]] = albums[sku["album"]]
            if sku["bullets"]["description_id"]:
                new_item["items"][0]["bullets"]["description"][sku["bullets"]["description_id"]] = descriptions[sku["bullets"]["description_id"]]
            if sku["bullets"]["feature_id"]:
                new_item["items"][0]["bullets"]["feature"][sku["bullets"]["feature_id"]] = features[sku["bullets"]["feature_id"]]
            if sku["bullets"]["spec_id"]:
                new_item["items"][0]["bullets"]["spec"][sku["bullets"]["spec_id"]] = specs[sku["bullets"]["spec_id"]]
            if sku["bullets"]["title_id"]:
                new_item["items"][0]["bullets"]["title"][sku["bullets"]["title_id"]] = titles[sku["bullets"]["title_id"]]

    items.append(new_item)
    return items