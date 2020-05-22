# Credsniper
## GitHub Module

__Maintainer:__ audibleblink (@4lex)

__Note:__ Only for OTP-protected accounts.

Module for intercepting GitHub credentials. Given the technical knowledge of the targets, this
module doesn't downgrade to SMS if it's available. That means it captures the OTP but it only lasts
30 seconds, in the best case scenario.

In order to steal access, this module actually logs the user into GitHub and stores the session
cookies to disk in CredSniper's root directory as `$username.sess`. From here, use your browser's
cookie manager to input the cookies and refresh github.com.
