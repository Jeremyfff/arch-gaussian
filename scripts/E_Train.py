from diffusers import DiffusionPipeline
import torch
import torchvision
from model import *

device = 'cuda' if torch.cuda.is_available() else 'cpu'

pipeline = DiffusionPipeline.from_pretrained(
    'lansinuote/diffsion_from_scratch.params', safety_checker=None)

scheduler = pipeline.scheduler
tokenizer = pipeline.tokenizer

del pipeline

#加载数据集
dataset = load_dataset(path='lansinuote/diffsion_from_scratch', split='train')


#图像增强模块
compose = torchvision.transforms.Compose([
    torchvision.transforms.Resize(
        512, interpolation=torchvision.transforms.InterpolationMode.BILINEAR),
    torchvision.transforms.CenterCrop(512),
    #torchvision.transforms.RandomHorizontalFlip(),
    torchvision.transforms.ToTensor(),
    torchvision.transforms.Normalize([0.5], [0.5]),
])

def f(data):
    #应用图像增强
    pixel_values = [compose(i) for i in data['image']]

    #文字编码
    input_ids = tokenizer.batch_encode_plus(data['text'],
                                            padding='max_length',
                                            truncation=True,
                                            max_length=77).input_ids

    return {'pixel_values': pixel_values, 'input_ids': input_ids}

dataset = dataset.map(f,
                      batched=True,
                      batch_size=100,
                      num_proc=1,
                      remove_columns=['image', 'text'])

dataset.set_format(type='torch')

#定义loader
def collate_fn(data):
    pixel_values = [i['pixel_values'] for i in data]
    input_ids = [i['input_ids'] for i in data]

    pixel_values = torch.stack(pixel_values).to(device)
    input_ids = torch.stack(input_ids).to(device)

    return {'pixel_values': pixel_values, 'input_ids': input_ids}


loader = torch.utils.data.DataLoader(dataset,
                                     shuffle=True,
                                     collate_fn=collate_fn,
                                     batch_size=1)


#准备训练
encoder.requires_grad_(False)
vae.requires_grad_(False)
unet.requires_grad_(True)

encoder.eval()
vae.eval()
unet.train()

encoder.to(device)
vae.to(device)
unet.to(device)

optimizer = torch.optim.AdamW(unet.parameters(),
                              lr=1e-5,
                              betas=(0.9, 0.999),
                              weight_decay=0.01,
                              eps=1e-8)

criterion = torch.nn.MSELoss()

def get_loss(data):
    with torch.no_grad():
        #文字编码
        #[1, 77] -> [1, 77, 768]
        out_encoder = encoder(data['input_ids'])

        #抽取图像特征图
        #[1, 3, 512, 512] -> [1, 4, 64, 64]
        out_vae = vae.encoder(data['pixel_values'])
        out_vae = vae.sample(out_vae)

        #0.18215 = vae.config.scaling_factor
        out_vae = out_vae * 0.18215

    #随机数,unet的计算目标
    noise = torch.randn_like(out_vae)

    #往特征图中添加噪声
    #1000 = scheduler.num_train_timesteps
    #1 = batch size
    noise_step = torch.randint(0, 1000, (1, )).long().to(device)
    out_vae_noise = scheduler.add_noise(out_vae, noise, noise_step)

    #根据文字信息,把特征图中的噪声计算出来
    out_unet = unet(out_vae=out_vae_noise,
                    out_encoder=out_encoder,
                    time=noise_step)

    #计算mse loss
    #[1, 4, 64, 64],[1, 4, 64, 64]
    return criterion(out_unet, noise)

def train():
    loss_sum = 0
    for epoch in range(400):
        for i, data in enumerate(loader):
            loss = get_loss(data) / 4
            loss.backward()
            loss_sum += loss.item()

            if (epoch * len(loader) + i) % 4 == 0:
                torch.nn.utils.clip_grad_norm_(unet.parameters(), 1.0)
                optimizer.step()
                optimizer.zero_grad()

        if epoch % 10 == 0:
            print(epoch, loss_sum)
            loss_sum = 0

    #torch.save(unet.to('cpu'), 'saves/unet.model')


train()