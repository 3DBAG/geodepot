"""License information for Geodepot and its bundled dependencies."""

from click import echo


LICENSES = """# Third-Party Licenses

This document lists the licenses of third-party software bundled with Geodepot release distributions.

## Geodepot

**License**: Apache License 2.0

See LICENSE file in the root directory of this distribution.

---

## Bundled Dependencies

### Geospatial Libraries

#### PROJ
- **Version**: 9.x
- **License**: MIT
- **URL**: https://proj.org/
- **Description**: Cartographic projections library

MIT License: Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including without
limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom
the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

#### GDAL (Geospatial Data Abstraction Library)
- **Version**: 3.9.x
- **License**: MIT / X11
- **URL**: https://gdal.org/
- **Description**: Translator library for raster and vector geospatial data formats

MIT/X11 License: Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including without
limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom
the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

#### PDAL (Point Data Abstraction Library)
- **Version**: 3.4.x
- **License**: BSD 3-Clause
- **URL**: https://pdal.io/
- **Description**: Point cloud data abstraction and processing library

BSD 3-Clause License: Redistribution and use in source and binary forms, with
or without modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

### Python Runtime

#### Python
- **Version**: 3.12.x
- **License**: PSF License
- **URL**: https://www.python.org/
- **Description**: Python programming language runtime

The Python Software Foundation License is available at https://docs.python.org/3/license.html

### Python Packages

#### Click
- **Version**: 8.1.x
- **License**: BSD 3-Clause
- **URL**: https://click.palletsprojects.com/
- **Description**: Python package for creating command-line interfaces

#### Requests
- **Version**: 2.32.x
- **License**: Apache License 2.0
- **URL**: https://requests.readthedocs.io/
- **Description**: Python HTTP library

#### Fabric
- **Version**: 3.2.x
- **License**: BSD 3-Clause
- **URL**: https://www.fabfile.org/
- **Description**: Python library for SSH command execution

---

## License Compliance Summary

| License Type | Components |
|---|---|
| Apache License 2.0 | Geodepot, Requests |
| MIT / MIT-X11 | PROJ, GDAL |
| BSD 3-Clause | PDAL, Click, Fabric |
| PSF License | Python |

All licenses are permissive and allow:
- ✓ Commercial use
- ✓ Modification
- ✓ Distribution
- ✓ Bundling

---

For complete license information, see THIRD_PARTY_LICENSES.md in the repository.
"""


def print_licenses(ctx, param, value):
    """Callback to print licenses and exit."""
    if value:
        echo(LICENSES)
        ctx.exit()
