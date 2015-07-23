# fin-lat-rep

This repository collects some resources for preparing the article on
representing small lattices as congruence lattices of finite algebras.  The
LaTeX files for the article itself are in the
[article directory](https://github.com/UniversalAlgebra/fin-lat-rep/tree/master/article).

Visitors, for questions, comments, or suggestions please contact the authors listed below,
or post a message on the
[wiki pages](https://github.com/UniversalAlgebra/fin-lat-rep/wiki),
or [submit an issue][].

Authors, to keep track of todo items use the [issue tracker][], or post
your comments on the [wiki pages](https://github.com/UniversalAlgebra/fin-lat-rep/wiki).

## Magit workflow
This section describes a few basic commands for committing and pushing changes
directly from Emacs using magit.

### To install magit

1. Put the following in your .emacs file:

        ;;
        ;; For Magit
    	;;
    	(setq package-archives '(("gnu" . "http://elpa.gnu.org/packages/")
        ("marmalade" . "http://marmalade-repo.org/packages/")
        ("melpa" . "http://melpa.milkbox.net/packages/")))
    	;; If you want to use magit, install the magit package
    	;; (if you haven't done so already) with the following commands:
    	;; \M package-refresh-contents
    	;; \M package-install [Enter] magit
    	(define-key global-map "\M-gm" 'magit-status)

   
2. Restart emacs and do

        M-x package-install <enter>
		magit <enter>

### use magit

1. Activate the magit status buffer with `M-x g m`.

2. Move the point down to appropriate line in the `Unstanged changes` section and
   hit the `s` key.

3. Type `c` `c`.

4. write a commit message, hopefully explaining why (not what) changes were
   made.

5. Type `C-c` `C-c` to commit the changes.

6. Type `P` `P` to push the changes to github.




[submit an issue]: https://github.com/UniversalAlgebra/fin-lat-rep/issues
[issue tracker]: https://github.com/UniversalAlgebra/fin-lat-rep/issues

