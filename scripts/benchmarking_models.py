import keras.applications as apps
from keras.models import Model,save_model


models = {
    # # size
    "resnet_50" : apps.ResNet50(),
    "nasnet_large" : apps.NASNetLarge(),
    "mobilenet" : apps.MobileNet(),

    # #parameters,
    "vgg_16" : apps.VGG16(),
    "resnet_101v2":apps.ResNet101V2(),
    "inception_v3" : apps.InceptionV3(),

    # #depth,
    "mobilenet_v2" : apps.MobileNetV2(),
    "efficientnet_v2b0" : apps.EfficientNetV2B0(),
    "efficientnet_v2l" : apps.EfficientNetV2L(),

    #steptime,
    "densenet_169" : apps.DenseNet169(),
    "densenet_201": apps.DenseNet201(),
    "nasnet_mobile" : apps.NASNetMobile(),
}


model_name:str
model:Model
for model_name,model in models.items():
    print(f"SAVING MODEL {model_name}")
    save_model(model,filepath=f"./models/{model_name}")


