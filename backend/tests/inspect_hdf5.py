import h5py, json

print('=== model_SARcarl.hdf5 input/output shapes ===')
with h5py.File('models/model_SARcarl.hdf5', 'r') as f:
    # Get all 4D kernels
    all_kernels = []
    def collect_kernels(name, obj):
        if hasattr(obj, 'shape') and len(obj.shape) == 4 and 'kernel' in name:
            all_kernels.append((name, obj.shape))
    f.visititems(collect_kernels)
    
    # Sort by conv number
    all_kernels.sort(key=lambda x: x[0])
    
    print('First kernel (input channels):')
    print(' ', all_kernels[0])
    
    print('Last kernel (output channels):')
    print(' ', all_kernels[-1])
    
    print()
    print(f'Total conv2d kernels: {len(all_kernels)}')
    
    # Check layer_names for input shape
    layer_names = f.attrs['layer_names']
    print()
    print('Layers order:', [n.decode() for n in layer_names[:10]])
    
    # Check input_1 and input_2
    for inp_name in ['input_1', 'input_2']:
        if inp_name in f:
            grp = f[inp_name]
            print(f'{inp_name} keys:', list(grp.keys()))
            for k in list(grp.keys()):
                sub = grp[k]
                if hasattr(sub, 'keys'):
                    print(f'  {k}:', list(sub.keys()))
        
    # Look at conv2d_34 (last one from layer names) and conv2d_33
    for conv_name in ['conv2d_34', 'conv2d_33', 'conv2d_32']:
        if conv_name in f:
            print(f'{conv_name} kernels:')
            def show_kernel(name, obj):
                if hasattr(obj, 'shape') and 'kernel' in name:
                    print(f'  {name}: {obj.shape}')
            f[conv_name].visititems(show_kernel)
