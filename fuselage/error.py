"""

Classes that represent errors within fuselage.

What is listed here are the exceptions raised within Python, with an
explanation of their meaning. If you wish to detect a specific error on
invocation, you can do so via the return code of the fuselage process.

All fuselage errors have a returncode, which is returned from the fuselage program
if these errors occur. This is primarily for the test harness, but feel free
to rely on these, they should be stable.

A returncode of less than 128 is an error from within the range specified in
the errno library, which contains the standard C error codes.

These may have been actually returned from a shell command, or they may be
based on our interpretation of the failure mode they represent. Resources will
define the errors they may return. """

import errno


class Error(Exception):
    """ Base class for all fuselage specific exceptions. """
    returncode = 253

    def __init__(self, msg=""):
        if msg:
            self.msg = msg

    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, self.msg)


class ParseError(Error):
    """ Root of exceptions that are caused by an error in input. """

    returncode = 128


class BindingError(Error):
    """ An error during policy binding. """

    returncode = 129


class ExecutionError(Error):
    """ Root of exceptions that are caused by execution failing in an unexpected way. """
    returncode = 130


class PackageError(ExecutionError):
    """ Error whilst performing a packaging error """
    returncode = 131


class CommandError(ExecutionError):
    """ A command from the Execute provider did not return the expected return
    code. """
    returncode = 133


class NoValidPolicy(ParseError):
    """ There is no valid policy for the resource. """

    returncode = 135


class NonConformingPolicy(ParseError):
    """ A policy has been specified, or has been chosen by default, but the
    parameters provided for the resource do not match those required for the
    policy. Check the documentation to ensure you have provided all required
    parameters. """
    returncode = 136


class NoSuitableProviders(ParseError):
    """ There are no suitable providers available for the policy and resource
    chosen. This may be because a provider has not been written for this
    Operating System or service, or it may be that you have not specified the
    parameters correctly. """
    msg = "There is no uitable provider for this resource/policy"
    returncode = 137


class TooManyProviders(ParseError):
    """ More than one provider matches the specified resource, and Yaybu is unable to choose between them. """
    returncode = 138


class InvalidProvider(ExecutionError):
    """ A provider is not valid. This is detected before any changes have been
    applied. """
    returncode = 139


class InvalidGroup(ExecutionError):
    """ The specified user group does not exist. """
    returncode = 140


class InvalidUser(ExecutionError):
    """ The specified user does not exist. """
    returncode = 141


class OperationFailed(ExecutionError):
    """ A general failure of an operation. For example, we tried to create a
    symlink, everything appeared to work but then a link does not exist. This
    should probably never happen. """
    returncode = 142


class BinaryMissing(ExecutionError):
    """ A specific error for an expected binary (ln, rm, etc.) not being
    present where expected. """
    returncode = 143


class DanglingSymlink(ExecutionError):
    """ The destination of a symbolic link does not exist. """
    returncode = 144


class UserAddError(ExecutionError):
    """ An error from the useradd command. It has a bunch of error codes of
    it's own. """
    returncode = 145


class PathComponentMissing(ExecutionError):
    """ A component of the path is not present """
    returncode = 146


class PathComponentNotDirectory(ExecutionError):
    """ A component of the path is in fact not a directory """
    returncode = 147


class SavedEventsAndNoInstruction(Error):
    """ There is a saved events file and the user has not decided what to do
    about it. Invoke with --resume or --no-resume. """
    returncode = 148
    msg = "There is a saved events file - you need to specify --resume or --no-resume"


class MissingAsset(ExecutionError):
    """ An asset referenced by a resource could not be found on the Yaybu
    search path. """
    returncode = 149


class CheckoutError(Error):
    """ An insurmountable problem was encountered during checkout """
    returncode = 150


class Incompatible(Error):
    """ An incompatibility was detected and execution can't continue """
    returncode = 151


class MissingDependency(ExecutionError):
    """ A dependency required for a feature or provider is missing """
    returncode = 152


class UnmodifiedAsset(ExecutionError):
    """ An asset was requested unnecesarily. This indicates an error in cache
    handling and should be filed as a bug against Yaybu. """
    returncode = 153


class NothingChanged(ExecutionError):
    """ Not really an error, but we need to know if this happens for our
    tests. This exception is never really raised, but it's useful to keep the
    error code here!"""
    msg = "No changes have been applied"
    returncode = 254


class SystemError(ExecutionError):
    """ An error represented by something in the errno list. """

    def __init__(self, returncode, stdout=None, stderr=None):
        # if the returncode is not in errno, this will blow up.
        try:
            self.msg = errno.errorcode[returncode]
        except KeyError:
            self.msg = "Exit code %s" % returncode
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
