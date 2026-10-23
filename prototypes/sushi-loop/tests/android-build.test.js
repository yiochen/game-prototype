import test from 'node:test';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

test('Android aapt2 audit reads SDK metadata and retains release and identity checks', () => {
  const builder = fileURLToPath(new URL('../tools/build_android.py', import.meta.url));
  execFileSync('python3', ['-c', String.raw`
import importlib.util, sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('android_build', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
branding = {'android_package':'com.example.sushi', 'version_code':52,
            'version_name':'0.4.12', 'title':'Sushi Loop'}
badging = """package: name='com.example.sushi' versionCode='52' versionName='0.4.12'
minSdkVersion:'24'
targetSdkVersion:'36'
application-label:'Sushi Loop'
feature-group: label=''
  uses-feature: name='android.hardware.vulkan.version'
"""
metadata = module.parse_apk_badging(badging, branding, 'release')
assert metadata['min_sdk'] == '24' and metadata['target_sdk'] == '36'
assert metadata['permissions'] == [] and metadata['debuggable'] is False
assert module.parse_apk_badging(badging.replace('minSdkVersion:', 'sdkVersion:'), branding, 'debug')['min_sdk'] == '24'
for corrupted in [badging.replace('com.example.sushi', 'com.other.game'),
                  badging.replace("versionCode='52'", "versionCode='51'"),
                  badging.replace("application-label:'Sushi Loop'", "application-label:'Other'"),
                  badging + "application-debuggable\n",
                  badging + "uses-permission: name='android.permission.INTERNET'\n",
                  badging + "  uses-permission: name='android.permission.INTERNET'\n"]:
    try:
        module.parse_apk_badging(corrupted, branding, 'release')
    except ValueError:
        continue
    raise AssertionError('Release audit accepted invalid metadata')
`, builder], { stdio: 'pipe', timeout: 10000 });
});
