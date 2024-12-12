from service.Pyclass import get_attr_val_by_spider_name


print("--------------------------------------------------------------------------------------------------------")
conf = get_attr_val_by_spider_name('custom_settings', 'lippioutdoor')
print(conf.get('FEED_EXPORT_FIELDS'))
