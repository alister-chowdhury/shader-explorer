import shader_explorer.rga

info = shader_explorer.rga.RGACompileInfo()
info.asic = "gfx1010"
# info.asic = "gfx900"
info.cs = r"C:\Users\thoth\Desktop\git\rendering-api\src\test\shader_compiling_0\out\encodeNumbersInplaceCS_0.spv"
info.output_dir = r"C:\Users\thoth\Desktop\a\ss\assasa"

res = shader_explorer.rga.rga_compile(info)

print(res["stdout"])

for k, m in res["shaders"].items():
    print(k)
    m.ensure_cfg_png_rendered()
    # for u, v in m.items():
    #     print(u,"=",v)