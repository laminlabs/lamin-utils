from __future__ import annotations

# BSD 3-Clause License
# Copyright (c) 2017-2018 P. Angerer, F. Alexander Wolf, Theis Lab
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import warnings
from functools import wraps


def deprecated(new_name=None, remove_in_version=None):
    """Decorator to mark functions as deprecated and hide them from docs.

    This is a decorator which can be used to mark functions, methods and properties as deprecated.
    It will result in a warning being emitted when the function is used.
    It will also hide the function from the docs.

    Args:
        new_name: Name of the new function to use instead.
            If `None`, omits the new name notice.
        remove_in_version: Version when this will be removed.
            If `None`, omits the remove in version X notice.

    Example:
        @property
        @deprecated("n_files")
        def n_objects(self) -> int:
            return self.n_files
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            base_msg = f"{func.__name__} is deprecated"
            version_msg = (
                f" and will be removed in version {remove_in_version}"
                if remove_in_version
                else ""
            )
            migration_msg = f". Use {new_name} instead" if new_name else ""
            msg = f"{base_msg}{version_msg}{migration_msg}."
            warnings.warn(msg, category=DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)

        setattr(wrapper, "__deprecated", True)
        return wrapper

    return decorator


def future_change(change_version=None, change_description=None):
    """Warns about future behavior changes.

    Args:
        change_version: Version when behavior will change.
        change_description: Description of the behavior change.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            base_msg = f"{func.__name__} behavior will change"
            version_msg = f" in version {change_version}" if change_version else ""
            desc_msg = f". {change_description}" if change_description else ""
            msg = f"{base_msg}{version_msg}{desc_msg}."
            warnings.warn(msg, category=FutureWarning, stacklevel=2)
            return func(*args, **kwargs)

        setattr(wrapper, "__future_change", True)
        return wrapper

    return decorator


def experimental(stable_version=None):
    """Marks function as experimental/unstable API.

    Args:
        stable_version: Expected version for API stabilization.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            base_msg = f"{func.__name__} is experimental"
            version_msg = f" until version {stable_version}" if stable_version else ""
            msg = f"{base_msg}{version_msg}. API may change without warning."
            warnings.warn(msg, category=UserWarning, stacklevel=2)
            return func(*args, **kwargs)

        setattr(wrapper, "__experimental", True)
        return wrapper

    return decorator
