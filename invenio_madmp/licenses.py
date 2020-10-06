"""Containers for information regarding licenses."""


class License:
    """Container for license information with utility methods."""

    uri_template = "https://opensource.org/licenses/%s"

    def __init__(self, identifier, name, uri=None, scheme=None):
        """Create a new license.

        :param identifier: The license identifier, e.g. 'BSD-3'
        :type identifier: str
        :param name: The full name of the license, e.g. '3-Clause BSD License'
        :type name: str
        :param uri: A URI pointing to the full text of the license
        :type uri: str, optional
        :param scheme: The license scheme, defaults to the identifier
        :type scheme: str, optional
        """
        self.identifier = identifier
        self.name = name
        self.scheme = scheme or identifier
        self.uri = uri or self.uri_template % self.identifier

        if self.identifier.endswith(".0"):
            self.short_identifier = self.identifier[:-2]
        else:
            self.short_identifier = self.identifier

        http, https = "http://", "https://"
        if self.uri.startswith(http):
            self.alt_uri = "%s%s" % (https, self.uri[len(http):])
        elif self.uri.startswith(https):
            self.alt_uri = "%s%s" % (http, self.uri[len(https):])

        self.values_to_check = [
            self.identifier,
            self.short_identifier,
            self.uri,
            self.alt_uri,
            self.scheme,
            self.name,
        ]

        if self.uri.endswith("/"):
            self.values_to_check.append(self.uri[:-1])

    def matches(self, *str_values):
        """Check if the license matches any of the provided str_values.

        Checks all provided values case-insensitively against the identifier
        (with and without the '.0' suffix, if such a suffix is present), URI,
        scheme and name of the license against any matches.
        :return: True, if the license matches any of the provided values.
        :rtype: bool
        """
        for val in (v.lower() for v in str_values):
            if val in (v.lower() for v in self.values_to_check):
                return True

        return False

    def to_dict(self):
        """Generate an RDM-Records-compliant dictionary from the License.

        :return: The License in dictionary form.
        :rtype: dict
        """
        return {
            "license": self.name,
            "uri": self.uri,
            "identifier": self.identifier,
            "scheme": self.scheme,
        }


class CCLicense(License):
    """Creative Commons licenses."""

    def matches(self, *str_values):
        """Check if the license matches any of the provided str_values."""
        if super().matches(*str_values):
            return True

        dashed_identifier = self.identifier.replace(" ", "-").lower()
        return any((val.lower() == dashed_identifier for val in str_values))


bsd_0 = License("0BSD", "Zero-Clause BSD")
bsd_1 = License("BSD-1-Clause", "1-Clause BSD License", scheme="BSD-1")
bsd_2 = License("BSD-2-Clause", "2-Clause BSD License", scheme="BSD-2")
bsd_3 = License("BSD-3-Clause", "3-Clause BSD License", scheme="BSD-3")
apache_2 = License("Apache-2.0", "Apache License, Version 2.0")
gpl_2 = License("GPL-2.0", "GNU General Public License Version 2")
gpl_3 = License("GPL-3.0", "GNU General Public License Version 3")
agpl_3 = License("AGPL-3.0", "GNU Affero General Public License Version 3")
lgpl_2 = License("LGPL-2.0", "GNU Library General Public License Version 2")
lgpl_2_1 = License("LGPL-2.1", "GNU Lesser General Public License Version 2.1")
lgpl_3 = License("LGPL-3.0", "GNU Lesser General Public License Version 2")
mit = License("MIT", "MIT License")
mit_0 = License("MIT-0", "MIT No Attribution License")
mpl_2 = License("MPL-2.0", "Mozilla Public License 2.0")
cddl = License("CDDL-1.0", "Common Development and Distribution License 1.0")
epl_2 = License("EPL-2.0", "Eclipse Public License Version 2.0")
unlicense = License("unlicense", "The Unlicense")

cc_0 = CCLicense(
    "CC0",
    "Public Domain Dedication",
    uri="https://creativecommons.org/publicdomain/zero/1.0/",
)
cc_by = CCLicense(
    "CC BY", "Attribution", uri="https://creativecommons.org/licenses/by/4.0/"
)
cc_by_sa = CCLicense(
    "CC BY-SA",
    "Attribution-ShareAlike",
    uri="https://creativecommons.org/licenses/by-sa/4.0/",
)
cc_by_nd = CCLicense(
    "CC BY-ND",
    "Attribution-NoDerivs",
    uri="https://creativecommons.org/licenses/by-nd/4.0/",
)
cc_by_nc = CCLicense(
    "CC BY-NC",
    "Attribution-NonCommercial",
    uri="https://creativecommons.org/licenses/by-nc/4.0/",
)
cc_by_nc_sa = CCLicense(
    "CC BY-NC-SA",
    "Attribution-NonCommercial-ShareAlike",
    uri="https://creativecommons.org/licenses/by-nc-sa/4.0/",
)
cc_by_nc_nd = CCLicense(
    "CC BY-NC-ND",
    "Attribution-NonCommercial-NoDerivs",
    uri="https://creativecommons.org/licenses/by-nc-nd/4.0/",
)

KNOWN_LICENSES = [
    bsd_0,
    bsd_1,
    bsd_2,
    bsd_3,
    apache_2,
    gpl_2,
    gpl_3,
    agpl_3,
    lgpl_2,
    lgpl_2_1,
    lgpl_3,
    mit,
    mit_0,
    mpl_2,
    cddl,
    epl_2,
    unlicense,
    cc_0,
    cc_by,
    cc_by_sa,
    cc_by_nd,
    cc_by_nc,
    cc_by_nc_sa,
    cc_by_nc_nd,
]
