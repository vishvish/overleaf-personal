// Initialize only a new replica set. Existing installations retain their data.
try {
  rs.status()
} catch (error) {
  if (error.code !== 94 && error.codeName !== 'NotYetInitialized') {
    throw error
  }
  const result = rs.initiate({
    _id: 'overleaf',
    members: [{ _id: 0, host: 'mongo:27017' }],
  })
  if (result.ok !== 1) {
    throw new Error('Unable to initialize MongoDB: ' + result.errmsg)
  }
}

const configuration = rs.conf()
if (configuration._id !== 'overleaf' ||
    configuration.members.length !== 1 ||
    configuration.members[0].host !== 'mongo:27017') {
  throw new Error('The saved MongoDB replica set does not match this installation.')
}

const deadline = Date.now() + 120000
while (Date.now() < deadline) {
  if (db.getSiblingDB('admin').runCommand({ hello: 1 }).isWritablePrimary) {
    print('MongoDB is ready.')
    quit(0)
  }
  sleep(1000)
}
throw new Error('MongoDB did not become writable within 120 seconds.')
