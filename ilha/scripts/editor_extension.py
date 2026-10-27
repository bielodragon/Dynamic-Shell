#!/usr/bin/env python3
"""Empacota uma extensão local VSIX sem npm, rede ou dependências de terceiros."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from xml.sax.saxutils import escape,quoteattr
import zipfile

SOURCE=Path(__file__).resolve().parents[1]/'integrations/vscode'


def build(output=None):
    manifest=json.loads((SOURCE/'package.json').read_text())
    if output is None:
        cache=Path(os.environ.get('XDG_CACHE_HOME',Path.home()/'.cache'))
        output=cache/'ilha/extensions'/('ilha-activities-'+manifest['version']+'.vsix')
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    attr=lambda value:quoteattr(str(value))
    xml='''<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
<Metadata><Identity Language="en-US" Id=%s Version=%s Publisher=%s/>
<DisplayName>%s</DisplayName><Description xml:space="preserve">%s</Description>
<Categories>Other</Categories><Properties>
<Property Id="Microsoft.VisualStudio.Code.Engine" Value=%s/>
<Property Id="Microsoft.VisualStudio.Code.ExtensionKind" Value="ui"/>
</Properties></Metadata><Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation>
<Dependencies/><Assets>
<Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>
<Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true"/>
<Asset Type="Microsoft.VisualStudio.Services.Content.License" Path="extension/LICENSE" Addressable="true"/>
</Assets></PackageManifest>'''%(attr(manifest['name']),attr(manifest['version']),attr(manifest['publisher']),
        escape(manifest['displayName']),escape(manifest['description']),attr(manifest['engines']['vscode']))
    content='''<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="json" ContentType="application/json"/><Default Extension="js" ContentType="application/javascript"/>
<Default Extension="md" ContentType="text/markdown"/><Default Extension="vsixmanifest" ContentType="text/xml"/>
<Override PartName="/extension/LICENSE" ContentType="text/plain"/></Types>'''
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('extension.vsixmanifest',xml);archive.writestr('[Content_Types].xml',content)
        for name in ('package.json','extension.js','activities.js','README.md','LICENSE'):
            archive.write(SOURCE/name,'extension/'+name)
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--install',choices=['code','codium'],help='Instala somente esta extensão no perfil padrão do editor escolhido.')
    args=parser.parse_args()
    try:
        output=build(args.output);print('Extensão local: '+str(output))
        if args.install:
            if os.geteuid()==0:raise ValueError('Instale a extensão como usuário, sem sudo.')
            executable=shutil.which(args.install)
            if not executable:raise ValueError('Editor não encontrado: '+args.install)
            subprocess.run([executable,'--install-extension',str(output),'--force'],check=True,timeout=90)
        return 0
    except (OSError,ValueError,subprocess.SubprocessError) as error:
        print(str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
