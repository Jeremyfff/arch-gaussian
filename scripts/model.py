print("importing...")
import torch
from transformers import CLIPTextModel
from diffusers import AutoencoderKL
from diffusers import UNet2DConditionModel


# region encoder
class Embed(torch.nn.Module):

    def __init__(self):
        super().__init__()

        self.embed = torch.nn.Embedding(49408, 768)
        self.pos_embed = torch.nn.Embedding(77, 768)

        self.register_buffer('pos_ids', torch.arange(77).unsqueeze(dim=0))

    def forward(self, input_ids):
        #input_ids -> [b, 77]

        #[b, 77] -> [b, 77, 768]
        embed = self.embed(input_ids)

        #[1, 77] -> [1, 77, 768]
        pos_embed = self.pos_embed(self.pos_ids)

        #[b, 77, 768]
        return embed + pos_embed

class Atten(torch.nn.Module):

    def __init__(self):
        super().__init__()
        self.q = torch.nn.Linear(768, 768)
        self.k = torch.nn.Linear(768, 768)
        self.v = torch.nn.Linear(768, 768)
        self.out = torch.nn.Linear(768, 768)

    def forward(self, x):
        #x -> [b, 77, 768]

        b = x.shape[0]

        #维度不变
        #[b, 77, 768]
        q = self.q(x) * 0.125
        k = self.k(x)
        v = self.v(x)

        #拆分注意力头
        #[b, 77, 768] -> [b, 77, 12, 64] -> [b, 12, 77, 64] -> [b*12, 77, 64]
        q = q.reshape(b, 77, 12, 64).transpose(1, 2).reshape(b * 12, 77, 64)
        k = k.reshape(b, 77, 12, 64).transpose(1, 2).reshape(b * 12, 77, 64)
        v = v.reshape(b, 77, 12, 64).transpose(1, 2).reshape(b * 12, 77, 64)

        #计算qk乘积
        #[b*12, 77, 64] * [b*12, 64, 77] -> [b*12, 77, 77]
        attn = torch.bmm(q, k.transpose(1, 2))

        #[b*12, 77, 77] -> [b, 12, 77, 77]
        attn = attn.reshape(b, 12, 77, 77)

        #覆盖mask
        def get_mask(b):
            mask = torch.empty(b, 77, 77)

            #上三角的部分置为负无穷
            mask.fill_(-float('inf'))

            #对角线和以下的位置为0
            mask.triu_(1)

            return mask.unsqueeze(1)

        #[b, 12, 77, 77] + [b, 1, 77, 77] -> [b, 12, 77, 77]
        attn = attn + get_mask(attn.shape[0]).to(attn.device)

        #[b, 12, 77, 77] -> [b*12, 77, 77]
        attn = attn.reshape(b * 12, 77, 77)

        #计算softmax,被mask的部分值为0
        attn = attn.softmax(dim=-1)

        #计算和v的乘积
        #[b*12, 77, 77] * [b*12, 77, 64] -> [b*12, 77, 64]
        attn = torch.bmm(attn, v)

        #[b*12, 77, 64] -> [b, 12, 77, 64] -> [b, 77, 12, 64] -> [b, 77, 768]
        attn = attn.reshape(b, 12, 77, 64).transpose(1, 2).reshape(b, 77, 768)

        #线性输出,维度不变
        #[b, 77, 768]
        return self.out(attn)

class ClipEncoder(torch.nn.Module):

    def __init__(self):
        super().__init__()

        self.s1 = torch.nn.Sequential(
            torch.nn.LayerNorm(768),
            Atten(),
        )

        self.s2 = torch.nn.Sequential(
            torch.nn.LayerNorm(768),
            torch.nn.Linear(768, 3072),
        )

        self.s3 = torch.nn.Linear(3072, 768)

    def forward(self, x):
        #x -> [2, 77, 768]

        #维度不变
        #[2, 77, 768]
        x = x + self.s1(x)

        #[2, 77, 768]
        res = x

        #[2, 77, 768] -> [2, 77, 3072]
        x = self.s2(x)

        #维度不变
        #[2, 77, 3072]
        x = x * (x * 1.702).sigmoid()

        #[2, 77, 3072] -> [2, 77, 768]
        return res + self.s3(x)

encoder = torch.nn.Sequential(
    Embed(),
    ClipEncoder(),
    ClipEncoder(),
    ClipEncoder(),
    ClipEncoder(),
    ClipEncoder(),
    ClipEncoder(),
    ClipEncoder(),
    ClipEncoder(),
    ClipEncoder(),
    ClipEncoder(),
    ClipEncoder(),
    ClipEncoder(),
    torch.nn.LayerNorm(768),
)


#=======加载预训练模型的参数=========
params = CLIPTextModel.from_pretrained(
    'lansinuote/diffsion_from_scratch.params', subfolder='text_encoder')

#词编码
encoder[0].embed.load_state_dict(
    params.text_model.embeddings.token_embedding.state_dict())

#位置编码
encoder[0].pos_embed.load_state_dict(
    params.text_model.embeddings.position_embedding.state_dict())

#12层编码层
for i in range(12):

    #第一层norm
    encoder[i + 1].s1[0].load_state_dict(
        params.text_model.encoder.layers[i].layer_norm1.state_dict())

    #注意力q矩阵
    encoder[i + 1].s1[1].q.load_state_dict(
        params.text_model.encoder.layers[i].self_attn.q_proj.state_dict())

    #注意力k矩阵
    encoder[i + 1].s1[1].k.load_state_dict(
        params.text_model.encoder.layers[i].self_attn.k_proj.state_dict())

    #注意力v矩阵
    encoder[i + 1].s1[1].v.load_state_dict(
        params.text_model.encoder.layers[i].self_attn.v_proj.state_dict())

    #注意力out
    encoder[i + 1].s1[1].out.load_state_dict(
        params.text_model.encoder.layers[i].self_attn.out_proj.state_dict())

    #第二层norm
    encoder[i + 1].s2[0].load_state_dict(
        params.text_model.encoder.layers[i].layer_norm2.state_dict())

    #mlp第一层fc
    encoder[i + 1].s2[1].load_state_dict(
        params.text_model.encoder.layers[i].mlp.fc1.state_dict())

    #mlp第二层fc
    encoder[i + 1].s3.load_state_dict(
        params.text_model.encoder.layers[i].mlp.fc2.state_dict())

#输出norm
encoder[13].load_state_dict(params.text_model.final_layer_norm.state_dict())

# endregion

# region vae
class Resnet(torch.nn.Module):

    def __init__(self, dim_in, dim_out):
        super().__init__()

        self.s = torch.nn.Sequential(
            torch.nn.GroupNorm(num_groups=32,
                               num_channels=dim_in,
                               eps=1e-6,
                               affine=True),
            torch.nn.SiLU(),
            torch.nn.Conv2d(dim_in,
                            dim_out,
                            kernel_size=3,
                            stride=1,
                            padding=1),
            torch.nn.GroupNorm(num_groups=32,
                               num_channels=dim_out,
                               eps=1e-6,
                               affine=True),
            torch.nn.SiLU(),
            torch.nn.Conv2d(dim_out,
                            dim_out,
                            kernel_size=3,
                            stride=1,
                            padding=1),
        )

        self.res = None
        if dim_in != dim_out:
            self.res = torch.nn.Conv2d(dim_in,
                                       dim_out,
                                       kernel_size=1,
                                       stride=1,
                                       padding=0)

    def forward(self, x):
        #x -> [1, 128, 10, 10]

        res = x
        if self.res:
            #[1, 128, 10, 10] -> [1, 256, 10, 10]
            res = self.res(x)

        #[1, 128, 10, 10] -> [1, 256, 10, 10]
        return res + self.s(x)

class Atten(torch.nn.Module):

    def __init__(self):
        super().__init__()
        self.norm = torch.nn.GroupNorm(num_channels=512,
                                       num_groups=32,
                                       eps=1e-6,
                                       affine=True)

        self.q = torch.nn.Linear(512, 512)
        self.k = torch.nn.Linear(512, 512)
        self.v = torch.nn.Linear(512, 512)
        self.out = torch.nn.Linear(512, 512)

    def forward(self, x):
        #x -> [1, 512, 64, 64]
        res = x

        #norm,维度不变
        #[1, 512, 64, 64]
        x = self.norm(x)

        #[1, 512, 64, 64] -> [1, 512, 4096] -> [1, 4096, 512]
        x = x.flatten(start_dim=2).transpose(1, 2)

        #线性运算,维度不变
        #[1, 4096, 512]
        q = self.q(x)
        k = self.k(x)
        v = self.v(x)

        #[1, 4096, 512] -> [1, 512, 4096]
        k = k.transpose(1, 2)

        #[1, 4096, 512] * [1, 512, 4096] -> [1, 4096, 4096]
        #0.044194173824159216 = 1 / 512**0.5
        #atten = q.bmm(k) * 0.044194173824159216

        #照理来说应该是等价的,但是却有很小的误差
        atten = torch.baddbmm(torch.empty(1, 4096, 4096, device=q.device),
                              q,
                              k,
                              beta=0,
                              alpha=0.044194173824159216)

        atten = torch.softmax(atten, dim=2)

        #[1, 4096, 4096] * [1, 4096, 512] -> [1, 4096, 512]
        atten = atten.bmm(v)

        #线性运算,维度不变
        #[1, 4096, 512]
        atten = self.out(atten)

        #[1, 4096, 512] -> [1, 512, 4096] -> [1, 512, 64, 64]
        atten = atten.transpose(1, 2).reshape(-1, 512, 64, 64)

        #残差连接,维度不变
        #[1, 512, 64, 64]
        atten = atten + res

        return atten

class Pad(torch.nn.Module):

    def forward(self, x):
        return torch.nn.functional.pad(x, (0, 1, 0, 1),
                                       mode='constant',
                                       value=0)

class VAE(torch.nn.Module):

    def __init__(self):
        super().__init__()

        self.encoder = torch.nn.Sequential(
            #in
            torch.nn.Conv2d(3, 128, kernel_size=3, stride=1, padding=1),

            #down
            torch.nn.Sequential(
                Resnet(128, 128),
                Resnet(128, 128),
                torch.nn.Sequential(
                    Pad(),
                    torch.nn.Conv2d(128, 128, 3, stride=2, padding=0),
                ),
            ),
            torch.nn.Sequential(
                Resnet(128, 256),
                Resnet(256, 256),
                torch.nn.Sequential(
                    Pad(),
                    torch.nn.Conv2d(256, 256, 3, stride=2, padding=0),
                ),
            ),
            torch.nn.Sequential(
                Resnet(256, 512),
                Resnet(512, 512),
                torch.nn.Sequential(
                    Pad(),
                    torch.nn.Conv2d(512, 512, 3, stride=2, padding=0),
                ),
            ),
            torch.nn.Sequential(
                Resnet(512, 512),
                Resnet(512, 512),
            ),

            #mid
            torch.nn.Sequential(
                Resnet(512, 512),
                Atten(),
                Resnet(512, 512),
            ),

            #out
            torch.nn.Sequential(
                torch.nn.GroupNorm(num_channels=512, num_groups=32, eps=1e-6),
                torch.nn.SiLU(),
                torch.nn.Conv2d(512, 8, 3, padding=1),
            ),

            #正态分布层
            torch.nn.Conv2d(8, 8, 1),
        )

        self.decoder = torch.nn.Sequential(
            #正态分布层
            torch.nn.Conv2d(4, 4, 1),

            #in
            torch.nn.Conv2d(4, 512, kernel_size=3, stride=1, padding=1),

            #middle
            torch.nn.Sequential(Resnet(512, 512), Atten(), Resnet(512, 512)),

            #up
            torch.nn.Sequential(
                Resnet(512, 512),
                Resnet(512, 512),
                Resnet(512, 512),
                torch.nn.Upsample(scale_factor=2.0, mode='nearest'),
                torch.nn.Conv2d(512, 512, kernel_size=3, padding=1),
            ),
            torch.nn.Sequential(
                Resnet(512, 512),
                Resnet(512, 512),
                Resnet(512, 512),
                torch.nn.Upsample(scale_factor=2.0, mode='nearest'),
                torch.nn.Conv2d(512, 512, kernel_size=3, padding=1),
            ),
            torch.nn.Sequential(
                Resnet(512, 256),
                Resnet(256, 256),
                Resnet(256, 256),
                torch.nn.Upsample(scale_factor=2.0, mode='nearest'),
                torch.nn.Conv2d(256, 256, kernel_size=3, padding=1),
            ),
            torch.nn.Sequential(
                Resnet(256, 128),
                Resnet(128, 128),
                Resnet(128, 128),
            ),

            #out
            torch.nn.Sequential(
                torch.nn.GroupNorm(num_channels=128, num_groups=32, eps=1e-6),
                torch.nn.SiLU(),
                torch.nn.Conv2d(128, 3, 3, padding=1),
            ),
        )

    def sample(self, h):
        #h -> [1, 8, 64, 64]

        #[1, 4, 64, 64]
        mean = h[:, :4]
        logvar = h[:, 4:]
        std = logvar.exp()**0.5

        #[1, 4, 64, 64]
        h = torch.randn(mean.shape, device=mean.device)
        h = mean + std * h

        return h

    def forward(self, x):
        #x -> [1, 3, 512, 512]

        #[1, 3, 512, 512] -> [1, 8, 64, 64]
        h = self.encoder(x)

        #[1, 8, 64, 64] -> [1, 4, 64, 64]
        h = self.sample(h)

        #[1, 4, 64, 64] -> [1, 3, 512, 512]
        h = self.decoder(h)

        return h

#加载预训练模型的参数
params = AutoencoderKL.from_pretrained(
    'lansinuote/diffsion_from_scratch.params', subfolder='vae')

vae = VAE()


def load_res(model, param):
    model.s[0].load_state_dict(param.norm1.state_dict())
    model.s[2].load_state_dict(param.conv1.state_dict())
    model.s[3].load_state_dict(param.norm2.state_dict())
    model.s[5].load_state_dict(param.conv2.state_dict())

    if isinstance(model.res, torch.nn.Module):
        model.res.load_state_dict(param.conv_shortcut.state_dict())


def load_atten(model, param):
    model.norm.load_state_dict(param.group_norm.state_dict())
    model.q.load_state_dict(param.query.state_dict())
    model.k.load_state_dict(param.key.state_dict())
    model.v.load_state_dict(param.value.state_dict())
    model.out.load_state_dict(param.proj_attn.state_dict())


#encoder.in
vae.encoder[0].load_state_dict(params.encoder.conv_in.state_dict())

#encoder.down
for i in range(4):
    load_res(vae.encoder[i + 1][0], params.encoder.down_blocks[i].resnets[0])
    load_res(vae.encoder[i + 1][1], params.encoder.down_blocks[i].resnets[1])

    if i != 3:
        vae.encoder[i + 1][2][1].load_state_dict(
            params.encoder.down_blocks[i].downsamplers[0].conv.state_dict())

#encoder.mid
load_res(vae.encoder[5][0], params.encoder.mid_block.resnets[0])
load_res(vae.encoder[5][2], params.encoder.mid_block.resnets[1])
load_atten(vae.encoder[5][1], params.encoder.mid_block.attentions[0])

#encoder.out
vae.encoder[6][0].load_state_dict(params.encoder.conv_norm_out.state_dict())
vae.encoder[6][2].load_state_dict(params.encoder.conv_out.state_dict())

#encoder.正态分布层
vae.encoder[7].load_state_dict(params.quant_conv.state_dict())

#decoder.正态分布层
vae.decoder[0].load_state_dict(params.post_quant_conv.state_dict())

#decoder.in
vae.decoder[1].load_state_dict(params.decoder.conv_in.state_dict())

#decoder.mid
load_res(vae.decoder[2][0], params.decoder.mid_block.resnets[0])
load_res(vae.decoder[2][2], params.decoder.mid_block.resnets[1])
load_atten(vae.decoder[2][1], params.decoder.mid_block.attentions[0])

#decoder.up
for i in range(4):
    load_res(vae.decoder[i + 3][0], params.decoder.up_blocks[i].resnets[0])
    load_res(vae.decoder[i + 3][1], params.decoder.up_blocks[i].resnets[1])
    load_res(vae.decoder[i + 3][2], params.decoder.up_blocks[i].resnets[2])

    if i != 3:
        vae.decoder[i + 3][4].load_state_dict(
            params.decoder.up_blocks[i].upsamplers[0].conv.state_dict())

#decoder.out
vae.decoder[7][0].load_state_dict(params.decoder.conv_norm_out.state_dict())
vae.decoder[7][2].load_state_dict(params.decoder.conv_out.state_dict())

data = torch.randn(1, 3, 512, 512)

a = vae.encoder(data)
b = params.encode(data).latent_dist.parameters

print((a == b).all())

data = torch.randn(1, 4, 64, 64)

a = vae.decoder(data)
b = params.decode(data).sample

print((a == b).all())
# endregion

# region unet
class Resnet(torch.nn.Module):

    def __init__(self, dim_in, dim_out):
        super().__init__()

        self.time = torch.nn.Sequential(
            torch.nn.SiLU(),
            torch.torch.nn.Linear(1280, dim_out),
            torch.nn.Unflatten(dim=1, unflattened_size=(dim_out, 1, 1)),
        )

        self.s0 = torch.nn.Sequential(
            torch.torch.nn.GroupNorm(num_groups=32,
                                     num_channels=dim_in,
                                     eps=1e-05,
                                     affine=True),
            torch.nn.SiLU(),
            torch.torch.nn.Conv2d(dim_in,
                                  dim_out,
                                  kernel_size=3,
                                  stride=1,
                                  padding=1),
        )

        self.s1 = torch.nn.Sequential(
            torch.torch.nn.GroupNorm(num_groups=32,
                                     num_channels=dim_out,
                                     eps=1e-05,
                                     affine=True),
            torch.nn.SiLU(),
            torch.torch.nn.Conv2d(dim_out,
                                  dim_out,
                                  kernel_size=3,
                                  stride=1,
                                  padding=1),
        )

        self.res = None
        if dim_in != dim_out:
            self.res = torch.torch.nn.Conv2d(dim_in,
                                             dim_out,
                                             kernel_size=1,
                                             stride=1,
                                             padding=0)

    def forward(self, x, time):
        #x -> [1, 320, 64, 64]
        #time -> [1, 1280]

        res = x

        #[1, 1280] -> [1, 640, 1, 1]
        time = self.time(time)

        #[1, 320, 64, 64] -> [1, 640, 32, 32]
        x = self.s0(x) + time

        #维度不变
        #[1, 640, 32, 32]
        x = self.s1(x)

        #[1, 320, 64, 64] -> [1, 640, 32, 32]
        if self.res:
            res = self.res(res)

        #维度不变
        #[1, 640, 32, 32]
        x = res + x

        return x

class CrossAttention(torch.nn.Module):

    def __init__(self, dim_q, dim_kv):
        #dim_q -> 320
        #dim_kv -> 768

        super().__init__()

        self.dim_q = dim_q

        self.q = torch.nn.Linear(dim_q, dim_q, bias=False)
        self.k = torch.nn.Linear(dim_kv, dim_q, bias=False)
        self.v = torch.nn.Linear(dim_kv, dim_q, bias=False)

        self.out = torch.nn.Linear(dim_q, dim_q)

    def forward(self, q, kv):
        #x -> [1, 4096, 320]
        #kv -> [1, 77, 768]

        #[1, 4096, 320] -> [1, 4096, 320]
        q = self.q(q)
        #[1, 77, 768] -> [1, 77, 320]
        k = self.k(kv)
        #[1, 77, 768] -> [1, 77, 320]
        v = self.v(kv)

        def reshape(x):
            #x -> [1, 4096, 320]
            b, lens, dim = x.shape

            #[1, 4096, 320] -> [1, 4096, 8, 40]
            x = x.reshape(b, lens, 8, dim // 8)

            #[1, 4096, 8, 40] -> [1, 8, 4096, 40]
            x = x.transpose(1, 2)

            #[1, 8, 4096, 40] -> [8, 4096, 40]
            x = x.reshape(b * 8, lens, dim // 8)

            return x

        #[1, 4096, 320] -> [8, 4096, 40]
        q = reshape(q)
        #[1, 77, 320] -> [8, 77, 40]
        k = reshape(k)
        #[1, 77, 320] -> [8, 77, 40]
        v = reshape(v)

        #[8, 4096, 40] * [8, 40, 77] -> [8, 4096, 77]
        #atten = q.bmm(k.transpose(1, 2)) * (self.dim_q // 8)**-0.5

        #从数学上是等价的,但是在实际计算时会产生很小的误差
        atten = torch.baddbmm(
            torch.empty(q.shape[0], q.shape[1], k.shape[1], device=q.device),
            q,
            k.transpose(1, 2),
            beta=0,
            alpha=(self.dim_q // 8)**-0.5,
        )

        atten = atten.softmax(dim=-1)

        #[8, 4096, 77] * [8, 77, 40] -> [8, 4096, 40]
        atten = atten.bmm(v)

        def reshape(x):
            #x -> [8, 4096, 40]
            b, lens, dim = x.shape

            #[8, 4096, 40] -> [1, 8, 4096, 40]
            x = x.reshape(b // 8, 8, lens, dim)

            #[1, 8, 4096, 40] -> [1, 4096, 8, 40]
            x = x.transpose(1, 2)

            #[1, 4096, 320]
            x = x.reshape(b // 8, lens, dim * 8)

            return x

        #[8, 4096, 40] -> [1, 4096, 320]
        atten = reshape(atten)

        #[1, 4096, 320] -> [1, 4096, 320]
        atten = self.out(atten)

        return atten

class Transformer(torch.nn.Module):

    def __init__(self, dim):
        super().__init__()

        self.dim = dim

        #in
        self.norm_in = torch.nn.GroupNorm(num_groups=32,
                                          num_channels=dim,
                                          eps=1e-6,
                                          affine=True)
        self.cnn_in = torch.nn.Conv2d(dim,
                                      dim,
                                      kernel_size=1,
                                      stride=1,
                                      padding=0)

        #atten
        self.norm_atten0 = torch.nn.LayerNorm(dim, elementwise_affine=True)
        self.atten1 = CrossAttention(dim, dim)
        self.norm_atten1 = torch.nn.LayerNorm(dim, elementwise_affine=True)
        self.atten2 = CrossAttention(dim, 768)

        #act
        self.norm_act = torch.nn.LayerNorm(dim, elementwise_affine=True)
        self.fc0 = torch.nn.Linear(dim, dim * 8)
        self.act = torch.nn.GELU()
        self.fc1 = torch.nn.Linear(dim * 4, dim)

        #out
        self.cnn_out = torch.nn.Conv2d(dim,
                                       dim,
                                       kernel_size=1,
                                       stride=1,
                                       padding=0)

    def forward(self, q, kv):
        #q -> [1, 320, 64, 64]
        #kv -> [1, 77, 768]
        b, _, h, w = q.shape
        res1 = q

        #----in----
        #维度不变
        #[1, 320, 64, 64]
        q = self.cnn_in(self.norm_in(q))

        #[1, 320, 64, 64] -> [1, 64, 64, 320] -> [1, 4096, 320]
        q = q.permute(0, 2, 3, 1).reshape(b, h * w, self.dim)

        #----atten----
        #维度不变
        #[1, 4096, 320]
        q = self.atten1(q=self.norm_atten0(q), kv=self.norm_atten0(q)) + q
        q = self.atten2(q=self.norm_atten1(q), kv=kv) + q

        #----act----
        #[1, 4096, 320]
        res2 = q

        #[1, 4096, 320] -> [1, 4096, 2560]
        q = self.fc0(self.norm_act(q))

        #1280
        d = q.shape[2] // 2

        #[1, 4096, 1280] * [1, 4096, 1280] -> [1, 4096, 1280]
        q = q[:, :, :d] * self.act(q[:, :, d:])

        #[1, 4096, 1280] -> [1, 4096, 320]
        q = self.fc1(q) + res2

        #----out----
        #[1, 4096, 320] -> [1, 64, 64, 320] -> [1, 320, 64, 64]
        q = q.reshape(b, h, w, self.dim).permute(0, 3, 1, 2).contiguous()

        #维度不变
        #[1, 320, 64, 64]
        q = self.cnn_out(q) + res1

        return q

class DownBlock(torch.nn.Module):

    def __init__(self, dim_in, dim_out):
        super().__init__()

        self.tf0 = Transformer(dim_out)
        self.res0 = Resnet(dim_in, dim_out)

        self.tf1 = Transformer(dim_out)
        self.res1 = Resnet(dim_out, dim_out)

        self.out = torch.nn.Conv2d(dim_out,
                                   dim_out,
                                   kernel_size=3,
                                   stride=2,
                                   padding=1)

    def forward(self, out_vae, out_encoder, time):
        outs = []

        out_vae = self.res0(out_vae, time)
        out_vae = self.tf0(out_vae, out_encoder)
        outs.append(out_vae)

        out_vae = self.res1(out_vae, time)
        out_vae = self.tf1(out_vae, out_encoder)
        outs.append(out_vae)

        out_vae = self.out(out_vae)
        outs.append(out_vae)

        return out_vae, outs

class UpBlock(torch.nn.Module):

    def __init__(self, dim_in, dim_out, dim_prev, add_up):
        super().__init__()

        self.res0 = Resnet(dim_out + dim_prev, dim_out)
        self.res1 = Resnet(dim_out + dim_out, dim_out)
        self.res2 = Resnet(dim_in + dim_out, dim_out)

        self.tf0 = Transformer(dim_out)
        self.tf1 = Transformer(dim_out)
        self.tf2 = Transformer(dim_out)

        self.out = None
        if add_up:
            self.out = torch.nn.Sequential(
                torch.nn.Upsample(scale_factor=2, mode='nearest'),
                torch.nn.Conv2d(dim_out, dim_out, kernel_size=3, padding=1),
            )

    def forward(self, out_vae, out_encoder, time, out_down):
        out_vae = self.res0(torch.cat([out_vae, out_down.pop()], dim=1), time)
        out_vae = self.tf0(out_vae, out_encoder)

        out_vae = self.res1(torch.cat([out_vae, out_down.pop()], dim=1), time)
        out_vae = self.tf1(out_vae, out_encoder)

        out_vae = self.res2(torch.cat([out_vae, out_down.pop()], dim=1), time)
        out_vae = self.tf2(out_vae, out_encoder)

        if self.out:
            out_vae = self.out(out_vae)

        return out_vae

class UNet(torch.nn.Module):

    def __init__(self):
        super().__init__()

        #in
        self.in_vae = torch.nn.Conv2d(4, 320, kernel_size=3, padding=1)

        self.in_time = torch.nn.Sequential(
            torch.nn.Linear(320, 1280),
            torch.nn.SiLU(),
            torch.nn.Linear(1280, 1280),
        )

        #down
        self.down_block0 = DownBlock(320, 320)
        self.down_block1 = DownBlock(320, 640)
        self.down_block2 = DownBlock(640, 1280)

        self.down_res0 = Resnet(1280, 1280)
        self.down_res1 = Resnet(1280, 1280)

        #mid
        self.mid_res0 = Resnet(1280, 1280)
        self.mid_tf = Transformer(1280)
        self.mid_res1 = Resnet(1280, 1280)

        #up
        self.up_res0 = Resnet(2560, 1280)
        self.up_res1 = Resnet(2560, 1280)
        self.up_res2 = Resnet(2560, 1280)

        self.up_in = torch.nn.Sequential(
            torch.nn.Upsample(scale_factor=2, mode='nearest'),
            torch.nn.Conv2d(1280, 1280, kernel_size=3, padding=1),
        )

        self.up_block0 = UpBlock(640, 1280, 1280, True)
        self.up_block1 = UpBlock(320, 640, 1280, True)
        self.up_block2 = UpBlock(320, 320, 640, False)

        #out
        self.out = torch.nn.Sequential(
            torch.nn.GroupNorm(num_channels=320, num_groups=32, eps=1e-5),
            torch.nn.SiLU(),
            torch.nn.Conv2d(320, 4, kernel_size=3, padding=1),
        )

    def forward(self, out_vae, out_encoder, time):
        #out_vae -> [1, 4, 64, 64]
        #out_encoder -> [1, 77, 768]
        #time -> [1]

        #----in----
        #[1, 4, 64, 64] -> [1, 320, 64, 64]
        out_vae = self.in_vae(out_vae)

        def get_time_embed(t):
            #-9.210340371976184 = -math.log(10000)
            e = torch.arange(160) * -9.210340371976184 / 160
            e = e.exp().to(t.device) * t

            #[160+160] -> [320] -> [1, 320]
            e = torch.cat([e.cos(), e.sin()]).unsqueeze(dim=0)

            return e

        #[1] -> [1, 320]
        time = get_time_embed(time)
        #[1, 320] -> [1, 1280]
        time = self.in_time(time)

        #----down----
        #[1, 320, 64, 64]
        #[1, 320, 64, 64]
        #[1, 320, 64, 64]
        #[1, 320, 32, 32]
        #[1, 640, 32, 32]
        #[1, 640, 32, 32]
        #[1, 640, 16, 16]
        #[1, 1280, 16, 16]
        #[1, 1280, 16, 16]
        #[1, 1280, 8, 8]
        #[1, 1280, 8, 8]
        #[1, 1280, 8, 8]
        out_down = [out_vae]

        #[1, 320, 64, 64],[1, 77, 768],[1, 1280] -> [1, 320, 32, 32]
        #out -> [1, 320, 64, 64],[1, 320, 64, 64][1, 320, 32, 32]
        out_vae, out = self.down_block0(out_vae=out_vae,
                                        out_encoder=out_encoder,
                                        time=time)
        out_down.extend(out)

        #[1, 320, 32, 32],[1, 77, 768],[1, 1280] -> [1, 640, 16, 16]
        #out -> [1, 640, 32, 32],[1, 640, 32, 32],[1, 640, 16, 16]
        out_vae, out = self.down_block1(out_vae=out_vae,
                                        out_encoder=out_encoder,
                                        time=time)
        out_down.extend(out)

        #[1, 640, 16, 16],[1, 77, 768],[1, 1280] -> [1, 1280, 8, 8]
        #out -> [1, 1280, 16, 16],[1, 1280, 16, 16],[1, 1280, 8, 8]
        out_vae, out = self.down_block2(out_vae=out_vae,
                                        out_encoder=out_encoder,
                                        time=time)
        out_down.extend(out)

        #[1, 1280, 8, 8],[1, 1280] -> [1, 1280, 8, 8]
        out_vae = self.down_res0(out_vae, time)
        out_down.append(out_vae)

        #[1, 1280, 8, 8],[1, 1280] -> [1, 1280, 8, 8]
        out_vae = self.down_res1(out_vae, time)
        out_down.append(out_vae)

        #----mid----
        #[1, 1280, 8, 8],[1, 1280] -> [1, 1280, 8, 8]
        out_vae = self.mid_res0(out_vae, time)

        #[1, 1280, 8, 8],[1, 77, 768] -> [1, 1280, 8, 8]
        out_vae = self.mid_tf(out_vae, out_encoder)

        #[1, 1280, 8, 8],[1, 1280] -> [1, 1280, 8, 8]
        out_vae = self.mid_res1(out_vae, time)

        #----up----
        #[1, 1280+1280, 8, 8],[1, 1280] -> [1, 1280, 8, 8]
        out_vae = self.up_res0(torch.cat([out_vae, out_down.pop()], dim=1),
                               time)

        #[1, 1280+1280, 8, 8],[1, 1280] -> [1, 1280, 8, 8]
        out_vae = self.up_res1(torch.cat([out_vae, out_down.pop()], dim=1),
                               time)

        #[1, 1280+1280, 8, 8],[1, 1280] -> [1, 1280, 8, 8]
        out_vae = self.up_res2(torch.cat([out_vae, out_down.pop()], dim=1),
                               time)

        #[1, 1280, 8, 8] -> [1, 1280, 16, 16]
        out_vae = self.up_in(out_vae)

        #[1, 1280, 16, 16],[1, 77, 768],[1, 1280] -> [1, 1280, 32, 32]
        #out_down -> [1, 640, 16, 16],[1, 1280, 16, 16],[1, 1280, 16, 16]
        out_vae = self.up_block0(out_vae=out_vae,
                                 out_encoder=out_encoder,
                                 time=time,
                                 out_down=out_down)

        #[1, 1280, 32, 32],[1, 77, 768],[1, 1280] -> [1, 640, 64, 64]
        #out_down -> [1, 320, 32, 32],[1, 640, 32, 32],[1, 640, 32, 32]
        out_vae = self.up_block1(out_vae=out_vae,
                                 out_encoder=out_encoder,
                                 time=time,
                                 out_down=out_down)

        #[1, 640, 64, 64],[1, 77, 768],[1, 1280] -> [1, 320, 64, 64]
        #out_down -> [1, 320, 64, 64],[1, 320, 64, 64],[1, 320, 64, 64]
        out_vae = self.up_block2(out_vae=out_vae,
                                 out_encoder=out_encoder,
                                 time=time,
                                 out_down=out_down)

        #----out----
        #[1, 320, 64, 64] -> [1, 4, 64, 64]
        out_vae = self.out(out_vae)

        return out_vae


#加载预训练模型的参数
params = UNet2DConditionModel.from_pretrained(
    'lansinuote/diffsion_from_scratch.params', subfolder='unet')

unet = UNet()

#in
unet.in_vae.load_state_dict(params.conv_in.state_dict())
unet.in_time[0].load_state_dict(params.time_embedding.linear_1.state_dict())
unet.in_time[2].load_state_dict(params.time_embedding.linear_2.state_dict())


#down
def load_tf(model, param):
    model.norm_in.load_state_dict(param.norm.state_dict())
    model.cnn_in.load_state_dict(param.proj_in.state_dict())

    model.atten1.q.load_state_dict(
        param.transformer_blocks[0].attn1.to_q.state_dict())
    model.atten1.k.load_state_dict(
        param.transformer_blocks[0].attn1.to_k.state_dict())
    model.atten1.v.load_state_dict(
        param.transformer_blocks[0].attn1.to_v.state_dict())
    model.atten1.out.load_state_dict(
        param.transformer_blocks[0].attn1.to_out[0].state_dict())

    model.atten2.q.load_state_dict(
        param.transformer_blocks[0].attn2.to_q.state_dict())
    model.atten2.k.load_state_dict(
        param.transformer_blocks[0].attn2.to_k.state_dict())
    model.atten2.v.load_state_dict(
        param.transformer_blocks[0].attn2.to_v.state_dict())
    model.atten2.out.load_state_dict(
        param.transformer_blocks[0].attn2.to_out[0].state_dict())

    model.fc0.load_state_dict(
        param.transformer_blocks[0].ff.net[0].proj.state_dict())

    model.fc1.load_state_dict(
        param.transformer_blocks[0].ff.net[2].state_dict())

    model.norm_atten0.load_state_dict(
        param.transformer_blocks[0].norm1.state_dict())
    model.norm_atten1.load_state_dict(
        param.transformer_blocks[0].norm2.state_dict())
    model.norm_act.load_state_dict(
        param.transformer_blocks[0].norm3.state_dict())

    model.cnn_out.load_state_dict(param.proj_out.state_dict())


def load_res(model, param):
    model.time[1].load_state_dict(param.time_emb_proj.state_dict())

    model.s0[0].load_state_dict(param.norm1.state_dict())
    model.s0[2].load_state_dict(param.conv1.state_dict())

    model.s1[0].load_state_dict(param.norm2.state_dict())
    model.s1[2].load_state_dict(param.conv2.state_dict())

    if isinstance(model.res, torch.nn.Module):
        model.res.load_state_dict(param.conv_shortcut.state_dict())


def load_down_block(model, param):
    load_tf(model.tf0, param.attentions[0])
    load_tf(model.tf1, param.attentions[1])

    load_res(model.res0, param.resnets[0])
    load_res(model.res1, param.resnets[1])

    model.out.load_state_dict(param.downsamplers[0].conv.state_dict())


load_down_block(unet.down_block0, params.down_blocks[0])
load_down_block(unet.down_block1, params.down_blocks[1])
load_down_block(unet.down_block2, params.down_blocks[2])

load_res(unet.down_res0, params.down_blocks[3].resnets[0])
load_res(unet.down_res1, params.down_blocks[3].resnets[1])

#mid
load_tf(unet.mid_tf, params.mid_block.attentions[0])
load_res(unet.mid_res0, params.mid_block.resnets[0])
load_res(unet.mid_res1, params.mid_block.resnets[1])

#up
load_res(unet.up_res0, params.up_blocks[0].resnets[0])
load_res(unet.up_res1, params.up_blocks[0].resnets[1])
load_res(unet.up_res2, params.up_blocks[0].resnets[2])
unet.up_in[1].load_state_dict(
    params.up_blocks[0].upsamplers[0].conv.state_dict())


def load_up_block(model, param):
    load_tf(model.tf0, param.attentions[0])
    load_tf(model.tf1, param.attentions[1])
    load_tf(model.tf2, param.attentions[2])

    load_res(model.res0, param.resnets[0])
    load_res(model.res1, param.resnets[1])
    load_res(model.res2, param.resnets[2])

    if isinstance(model.out, torch.nn.Module):
        model.out[1].load_state_dict(param.upsamplers[0].conv.state_dict())


load_up_block(unet.up_block0, params.up_blocks[1])
load_up_block(unet.up_block1, params.up_blocks[2])
load_up_block(unet.up_block2, params.up_blocks[3])

#out
unet.out[0].load_state_dict(params.conv_norm_out.state_dict())
unet.out[2].load_state_dict(params.conv_out.state_dict())

# validate
out_vae = torch.randn(1, 4, 64, 64)
out_encoder = torch.randn(1, 77, 768)
time = torch.LongTensor([26])

a = unet(out_vae=out_vae, out_encoder=out_encoder, time=time)
b = params(out_vae, time, out_encoder).sample

print((a == b).all())
# endregion

if __name__ == "__main__":
    pass