Ceefax: a listing for your stuff

The goal of Ceefax is to give a means to share files in a secure way.

THE DESIGN OF CEEFAX
--------------------

Ceefax is designed with these basic models in mind:

* Objects
* Repositories
* Collections
* Users

Objects
=======

Objects are any file that can be served up by Ceefax. An object has these attributes:

* Identifier
* Name
* SHA512 hash
* File meta data
* Owner repository
* Visibility

An objects identifier is a UUID; Theoretically, this is a Type 1 UUID, however any UUID type
is valid so long as it is consistent. Owner repository is expressed as the
identifier of the repository (see below)

Repositories
============

Repositories are the physical places where objects are stored on disk.

* Name
* Identifier
* Location (on disk)
* Visibility
* Owner User

A repository identifier is a UUID; As with Objects, this is usually a Type 1 UUID.
Name is a human-readable name. Owner User is a user ID.

Two repositories with the same location on disk may not exist.

Collections
==========

Collections are a selection of objects which may be from a variety of
repositories. Collections are described with the following:

* Name
* Identifier
* Visibility

The identifier of a collection is a type 1 UUID or any other 'unique' mechanism
to uniquely identify the object.

Users
=====

Users are -- just that, users. They are described as thus:

* User ID (numeric)
* User name (machine) -- a-z0-9 no spaces
* User name (human)   -- Any unicode string
* Hashed passphrase

Visibility of objects
=====================

Visibility of objects is determined by the following:

* Visibility as defined in the object (specific objects may be made public)
* Visibility as defined in a collection (collections may override the visibility of an object)
* Visibility of the repository (an object in a public repository is always public)

For example, let's consider an imaginary object. Let's assume its ID is {1234-123-32-43}.
When this object is requested, the following should occur:

 * check if the object exists (if not, return 404)
 * check if the repository the object belongs to belongs to the currently logged in user (if yes, return the object whole)
 * check if the object is specifically made public (if yes, return the object whole)
 * check if the object is in a collection which is public AND the collection is specified (if yes, return object whole)
 * check if object is in a repository which is marked as public (if yes, return object whole)
 * if this step reached, return a 403 unauthorized or 404 not found.

Visibility states
-----------------

An object, collection or repository may exist in three visibility states:

 * Public (listed in the public index for a user)
 * Protected (unlisted, but accessible via its identifier)
 * Private (only accessible by the owning user)

Operation of the database
=========================

The design of the schema is intended to allow objects to move between repositories as needed.
For example, a repository may be the latest photos from a camera, whereas an automated process
would move older photos into a repository which acts as an archive for these photos. This action
makes archival of photos from a synchronized collection of cell phone camera images better.

An object's URI should remain the same for the lifetime of the object. When an object moves from
one repository to another, the database should be updated to reflect that.

A system, such as inotify, should be used to monitor changes within the filesystem. At startup, a
full database audit should be done to make certain that objects are in their appropriate places.

Multiple objects with the same SHA512 may exist. The following logic describes handling an object:

( In the following, "existing" is defined by 'an object with that SHA512 hash exists')

 * If the object does not exist at all, add it.
 * If the object exists on disk AND in the current repositoriy but the SHA512 differs, update the SHA512
 * If the object exists and is in another repository, check that it physically exists on disk.
   - If the object in another repository exists, but is not on disk, update its repository.
   - If the object in another repository exists, but is on disk, add the current file to the current repository.

After objects are added, objects should be pruned. A sweep to remove objects which:

 * do not exist on disk
 * belong to a nonexistent repository
 * belong to a destroyed user
   ( When a user is destroyed, their repositories are removed )

URIs within the Ceefax hierarchy:

 * `/object/{id}` - A specific object. 
 * `/object/{id}?cid={id}` - An object, as a part of a collection.
 * `/collection/{id}` - a specific collection.
 * `/u:{uid}/` - a specific user
 * `/u:{uid}/{repo}` - a specific user's repo.


