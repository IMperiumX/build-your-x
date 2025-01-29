#! /usr/bin/env ruby
require 'fileutils'
require 'pathname'
require_relative 'workspace'
require_relative 'database'
require_relative 'blob'
require_relative 'entry'
require_relative 'tree'
require_relative 'author'
require_relative 'commit'
def usage
  puts 'usage: jit <command> [<args>]'
  puts
  puts 'The most commonly used jit commands are:'
  puts '   init        Create an empty Jit repository or reinitialize an existing one'
  puts
  puts "See 'jit help <command>' for more information on a specific command."
end

command = ARGV.shift
case command
when 'init'
  path = ARGV.fetch(0, Dir.getwd)
  root_path = Pathname.new(File.expand_path(path))
  git_path = root_path.join('.git')
  %w[objects refs].each do |dir|
    FileUtils.mkdir_p(git_path.join(dir))
  rescue Errno::EACCES => e
    warn "fatal: #{e.message}"
    exit 1
  end
  puts "Initialized empty Jit repository in #{git_path}"
  exit 0
when 'commit'
  root_path = Pathname.new(Dir.getwd)
  git_path = root_path.join('.git')
  db_path = git_path.join('objects')
  workspace = Workspace.new(root_path)
  database = Database.new(db_path)
  entries = workspace.list_files.map do |path|
    data = workspace.read_file(path)
    blob = Blob.new(data)
    database.store(blob)
    Entry.new(path, blob.oid)
  end
  tree = Tree.new(entries)
  database.store(tree)
  puts "tree: #{tree.oid}"
  name = ENV.fetch('GIT_AUTHOR_NAME', 'Yousef')
  email = ENV.fetch('GIT_AUTHOR_EMAIL', 'yusufadell.dev@gmail.com')
  author = Author.new(name, email, Time.now)
  message = $stdin.read
  commit = Commit.new(tree.oid, author, message)
  database.store(commit)
  File.open(git_path.join('HEAD'), File::WRONLY | File::CREAT) do |file|
    file.puts(commit.oid)
  end
  puts "[(root-commit) #{commit.oid}] #{message.lines.first}"
  exit 0
when 'help'
  subcommand = ARGV.shift
  case subcommand
  when 'init'
    puts 'usage: jit init [<path>]'
    puts
    puts 'Create an empty Jit repository or reinitialize an existing one'
    puts
    puts 'If <path> is specified, the repository is created at that path.'
    puts 'Otherwise, the repository is created in the current working directory.'
    exit 0
  else
    warn "jit: '#{subcommand}' is not a jit command. See 'jit --help'."
    exit 1
  end

when nil
  usage
  exit 1
else
  warn "jit: '#{command}' is not a jit command."
  exit 1
end
